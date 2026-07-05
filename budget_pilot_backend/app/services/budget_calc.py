import uuid
import datetime

from sqlalchemy.orm import Session

from app.crud import category_month as crud_month
from app.crud import purchase as crud_purchase
from app.crud import income as crud_income


def _days_in_month(month: str) -> int:
    year, mon = (int(p) for p in month.split("-"))
    if mon == 12:
        next_month = datetime.date(year + 1, 1, 1)
    else:
        next_month = datetime.date(year, mon + 1, 1)
    return (next_month - datetime.date(year, mon, 1)).days


def get_month_summary(db: Session, user_id: uuid.UUID, month: str, include_prev: bool = True) -> dict:
    """
    Everything the frontend needs to render one month, computed here instead
    of in React: total planned, total actual (rolled up live from purchases,
    not a stale cached number), how many days into the month we are, a
    'pace' per category, and (optionally) what was actually spent in the
    previous month for comparison.
    """
    rows = crud_month.get_month(db, user_id, month)
    spend_by_category = crud_purchase.sum_purchases_by_category(db, user_id, month)

    prev_actuals: dict = {}
    if include_prev:
        prev_month = _shift_month(month, -1)
        prev_summary = get_month_summary(db, user_id, prev_month, include_prev=False)
        prev_actuals = {c["category_id"]: c["actual_amount"] for c in prev_summary["categories"]}

    today = datetime.date.today()
    year, mon = (int(p) for p in month.split("-"))
    total_days = _days_in_month(month)
    if today.year == year and today.month == mon:
        days_elapsed = today.day
    elif datetime.date(year, mon, 1) < today:
        days_elapsed = total_days  # a past month is fully "elapsed"
    else:
        days_elapsed = 0  # a future month hasn't started
    pct_month_elapsed = days_elapsed / total_days if total_days else 0

    categories = []
    total_planned = 0.0
    total_actual = 0.0

    for row in rows:
        planned = row["planned_amount"]
        # Live actual = whatever was logged as purchases this month for this
        # category, falling back to the stored actual_amount for categories
        # (like SIP/Emergency Fund) that aren't purchase-based.
        actual = spend_by_category.get(row["category_id"], row["actual_amount"])

        # Rolling envelope carryover: what this category ran over/under by in
        # every month before this one. A positive carry_in means past surplus
        # (you can spend a bit more this month before it counts as "over");
        # negative means past overspend still needs to be absorbed.
        carry_in = crud_month.get_category_carryover(db, user_id, row["category_id"], month)
        balance = round(planned - actual, 2)
        cumulative_balance = round(carry_in + balance, 2)
        effective_planned = round(planned + carry_in, 2)

        expected_by_now = planned * pct_month_elapsed
        pace = "on_track"
        if planned > 0:
            if actual > planned:
                pace = "over_budget"
            elif actual > expected_by_now * 1.15:
                pace = "ahead_of_pace"

        categories.append(
            {
                "category_id": row["category_id"],
                "category_name": row["category_name"],
                "category_type": row["category_type"],
                "is_default": row["is_default"],
                "is_archived": row["is_archived"],
                "planned_amount": planned,
                "actual_amount": actual,
                "prev_month_actual": prev_actuals.get(row["category_id"]),
                "notes": row["notes"],
                "pace": pace,
                "balance": balance,
                "carry_in": carry_in,
                "cumulative_balance": cumulative_balance,
                "effective_planned": effective_planned,
            }
        )
        total_planned += planned
        total_actual += actual

    total_income = crud_income.total_income(db, user_id, month)
    # "Unplanned" = income not yet assigned to any category's planned amount.
    # Negative means the planned amounts already add up to more than the
    # income brought in this month -- i.e. the budget is over-committed.
    unplanned_amount = round(total_income - total_planned, 2)
    unplanned_pct = round((unplanned_amount / total_income) * 100, 1) if total_income else None
    leftover_amount = round(total_income - total_actual, 2)
    leftover_pct = round((leftover_amount / total_income) * 100, 1) if total_income else None
    planned_pct_of_income = round((total_planned / total_income) * 100, 1) if total_income else None
    spent_pct_of_income = round((total_actual / total_income) * 100, 1) if total_income else None

    return {
        "month": month,
        "days_elapsed": days_elapsed,
        "days_in_month": total_days,
        "total_planned": round(total_planned, 2),
        "total_actual": round(total_actual, 2),
        "total_income": round(total_income, 2),
        "unplanned_amount": unplanned_amount,
        "unplanned_pct": unplanned_pct,
        "leftover_amount": leftover_amount,
        "leftover_pct": leftover_pct,
        "planned_pct_of_income": planned_pct_of_income,
        "spent_pct_of_income": spent_pct_of_income,
        "over_committed": unplanned_amount < 0,
        "categories": categories,
    }


def _shift_month(month: str, delta: int) -> str:
    year, mon = (int(p) for p in month.split("-"))
    total = year * 12 + (mon - 1) + delta
    return f"{total // 12}-{(total % 12) + 1:02d}"


def get_history(db: Session, user_id: uuid.UUID, end_month: str, num_months: int = 12) -> list[dict]:
    """
    The last `num_months` months (oldest to newest, ending at end_month),
    each computed with the same get_month_summary used for the single-month
    view. This is what feeds the 12-month bar chart, and quarter/year
    rollups the frontend groups client-side from these same months.
    """
    months = [_shift_month(end_month, -i) for i in range(num_months - 1, -1, -1)]
    return [get_month_summary(db, user_id, m) for m in months]


def get_savings_lifetime(db: Session, user_id: uuid.UUID) -> list[dict]:
    """
    Lifetime total saved/invested per 'saving'-type category (Emergency Fund,
    SIP Investing, and any custom saving categories), summed across every
    month that's ever existed for that category -- not tied to the month
    navigator at all. Uses the same purchases-first-else-manual-actual logic
    as get_month_summary so a lifetime total always matches what each month
    displayed.
    """
    return crud_month.get_lifetime_savings(db, user_id)
