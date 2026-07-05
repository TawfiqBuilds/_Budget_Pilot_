import uuid

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.category import Category, CategoryType
from app.models.category_month import CategoryMonth


def get_month(db: Session, user_id: uuid.UUID, month: str) -> list[dict]:
    """
    Every active category shows up here automatically -- even ones that have
    never had a planned amount set for this month yet (defaulting to 0 until
    the user fills it in). Archived categories only show up if they already
    have a CategoryMonth row for this specific month (decision #2: archived
    categories are visible only in the months they were active in).
    """
    active_categories = list(
        db.scalars(
            select(Category)
            .where(Category.user_id == user_id, Category.is_archived.is_(False))
            .order_by(Category.sort_order, Category.created_at)
        )
    )

    existing_rows = {
        cm.category_id: cm
        for cm in db.scalars(
            select(CategoryMonth).where(CategoryMonth.user_id == user_id, CategoryMonth.month == month)
        )
    }

    results: list[dict] = []
    seen_category_ids: set[uuid.UUID] = set()

    for cat in active_categories:
        cm = existing_rows.get(cat.id)
        results.append(_to_dict(cat, cm, month))
        seen_category_ids.add(cat.id)

    # Any remaining CategoryMonth rows belong to archived categories -- only
    # include those that are actually for THIS month.
    for cat_id, cm in existing_rows.items():
        if cat_id in seen_category_ids:
            continue
        cat = db.get(Category, cat_id)
        if cat:
            results.append(_to_dict(cat, cm, month))

    return results


def _to_dict(cat: Category, cm: CategoryMonth | None, month: str) -> dict:
    return {
        "category_id": cat.id,
        "category_name": cat.name,
        "category_type": cat.type.value,
        "is_default": cat.is_default,
        "is_archived": cat.is_archived,
        "month": month,
        "planned_amount": float(cm.planned_amount) if cm else 0.0,
        "actual_amount": float(cm.actual_amount) if cm else 0.0,
        "notes": cm.notes if cm else "",
    }


def get_all_months_for_user(db: Session, user_id: uuid.UUID) -> list[str]:
    """Every distinct 'YYYY-MM' that has any CategoryMonth row at all, sorted."""
    rows = db.scalars(
        select(CategoryMonth.month).where(CategoryMonth.user_id == user_id).distinct()
    ).all()
    return sorted(rows)


def upsert_month_entry(
    db: Session,
    user_id: uuid.UUID,
    category_id: uuid.UUID,
    month: str,
    planned_amount: float | None = None,
    actual_amount: float | None = None,
    notes: str | None = None,
) -> CategoryMonth:
    row = db.scalar(
        select(CategoryMonth).where(
            CategoryMonth.user_id == user_id,
            CategoryMonth.category_id == category_id,
            CategoryMonth.month == month,
        )
    )
    if row is None:
        row = CategoryMonth(user_id=user_id, category_id=category_id, month=month)
        db.add(row)

    if planned_amount is not None:
        row.planned_amount = planned_amount
    if actual_amount is not None:
        row.actual_amount = actual_amount
    if notes is not None:
        row.notes = notes

    db.commit()
    db.refresh(row)
    return row


def get_lifetime_savings(db: Session, user_id: uuid.UUID) -> list[dict]:
    """
    Lifetime total saved/invested per 'saving'-type category (Emergency Fund,
    SIP Investing, any custom saving category) -- summed across every month
    that's ever existed for it, not tied to the month navigator.

    Uses the same purchases-first-else-manual-actual rule as get_month_summary
    per month, so this total is always consistent with what each month shows.
    """
    from app.crud import purchase as crud_purchase  # local import avoids a circular import

    # Archived categories with a lifetime total of 0 are excluded below (that
    # was the reported bug: an archived "saving for a dress" category with no
    # data kept showing up forever as a permanent "Dress -- lifetime Rs0" card).
    # An archived category that *does* have real lifetime savings still shows,
    # since hiding real money saved would be misleading.
    saving_categories = list(
        db.scalars(
            select(Category).where(Category.user_id == user_id, Category.type == CategoryType.saving)
        )
    )

    results = []
    for cat in saving_categories:
        cm_rows = db.scalars(
            select(CategoryMonth).where(CategoryMonth.category_id == cat.id, CategoryMonth.user_id == user_id)
        ).all()

        spend_by_month = crud_purchase.sum_purchases_by_month_for_category(db, user_id, cat.id)
        total = sum(spend_by_month.get(cm.month, float(cm.actual_amount)) for cm in cm_rows)

        if cat.is_archived and round(total, 2) == 0:
            continue

        results.append({"category_id": cat.id, "category_name": cat.name, "lifetime_total": round(total, 2)})

    return results


def list_all_archived(db: Session, user_id: uuid.UUID) -> list[Category]:
    """
    Every archived category for this user, regardless of whether it ever has
    a CategoryMonth row for the currently-viewed month. This is what makes an
    archived-with-zero-data category (which never shows up in any month view,
    since get_month() only surfaces archived categories for months they have
    a row in) reachable again in the UI -- otherwise "Restore" is impossible
    to find once a category like that is archived.
    """
    stmt = (
        select(Category)
        .where(Category.user_id == user_id, Category.is_archived.is_(True))
        .order_by(Category.sort_order, Category.created_at)
    )
    return list(db.scalars(stmt))


def get_category_carryover(db: Session, user_id: uuid.UUID, category_id: uuid.UUID, upto_month_exclusive: str) -> float:
    """
    Rolling envelope-style carryover: if you overspend a category one month,
    that deficit reduces next month's effective budget; if you underspend,
    the surplus adds to it -- and it keeps accumulating month over month
    until it's used up. This is what lets a one-off purchase like "Mysore
    trip, Rs180, but really a 3-month expense" be absorbed gradually: log it
    once, then quietly protect against overspending in the following months
    by shrinking what's "free" to spend until the deficit clears.

    Returns the carry-in balance for `upto_month_exclusive` (i.e. the
    accumulated planned-minus-actual from every month strictly before it,
    for this one category).
    """
    rows = list(
        db.scalars(
            select(CategoryMonth)
            .where(CategoryMonth.category_id == category_id, CategoryMonth.user_id == user_id)
            .order_by(CategoryMonth.month)
        )
    )
    if not rows:
        return 0.0

    from app.crud import purchase as crud_purchase  # local import avoids a circular import

    spend_by_month = crud_purchase.sum_purchases_by_month_for_category(db, user_id, category_id)

    carry = 0.0
    for row in rows:
        if row.month >= upto_month_exclusive:
            break
        actual = spend_by_month.get(row.month, float(row.actual_amount))
        carry += float(row.planned_amount) - actual
    return round(carry, 2)


def clone_previous_month(db: Session, user_id: uuid.UUID, from_month: str, to_month: str) -> list[CategoryMonth]:
    """Copies last month's planned amounts into a new month (doesn't touch actuals)."""
    prev_rows = db.scalars(
        select(CategoryMonth).where(CategoryMonth.user_id == user_id, CategoryMonth.month == from_month)
    ).all()
    created = []
    for prev in prev_rows:
        existing = db.scalar(
            select(CategoryMonth).where(
                CategoryMonth.user_id == user_id,
                CategoryMonth.category_id == prev.category_id,
                CategoryMonth.month == to_month,
            )
        )
        if existing:
            continue
        new_row = CategoryMonth(
            user_id=user_id,
            category_id=prev.category_id,
            month=to_month,
            planned_amount=prev.planned_amount,
            actual_amount=0,
            notes="",
        )
        db.add(new_row)
        created.append(new_row)
    db.commit()
    for r in created:
        db.refresh(r)
    return created
