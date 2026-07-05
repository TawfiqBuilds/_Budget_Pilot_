import uuid
import datetime

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.purchase import Purchase


def list_purchases(db: Session, user_id: uuid.UUID, month: str | None = None, category_id: uuid.UUID | None = None) -> list[Purchase]:
    stmt = select(Purchase).where(Purchase.user_id == user_id)
    if month:
        # month is "YYYY-MM" -> filter by that calendar month
        year, mon = (int(p) for p in month.split("-"))
        start = datetime.datetime(year, mon, 1, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(year + (mon == 12), (mon % 12) + 1, 1, tzinfo=datetime.timezone.utc)
        stmt = stmt.where(Purchase.date >= start, Purchase.date < end)
    if category_id:
        stmt = stmt.where(Purchase.category_id == category_id)
    stmt = stmt.order_by(Purchase.date.desc())
    return list(db.scalars(stmt))


def create_purchase(
    db: Session,
    user_id: uuid.UUID,
    category_id: uuid.UUID,
    name: str,
    amount: float,
    date: datetime.datetime | None = None,
) -> Purchase:
    purchase = Purchase(user_id=user_id, category_id=category_id, name=name.strip(), amount=amount)
    if date is not None:
        purchase.date = date
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


def delete_purchase(db: Session, user_id: uuid.UUID, purchase_id: uuid.UUID) -> None:
    purchase = db.scalar(select(Purchase).where(Purchase.id == purchase_id, Purchase.user_id == user_id))
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found.")
    db.delete(purchase)
    db.commit()


def sum_purchases_by_category(db: Session, user_id: uuid.UUID, month: str) -> dict[uuid.UUID, float]:
    """Used by budget_calc to roll actual spend into category_months."""
    year, mon = (int(p) for p in month.split("-"))
    start = datetime.datetime(year, mon, 1, tzinfo=datetime.timezone.utc)
    end = datetime.datetime(year + (mon == 12), (mon % 12) + 1, 1, tzinfo=datetime.timezone.utc)
    rows = db.execute(
        select(Purchase.category_id, func.sum(Purchase.amount))
        .where(Purchase.user_id == user_id, Purchase.date >= start, Purchase.date < end)
        .group_by(Purchase.category_id)
    ).all()
    return {cat_id: float(total) for cat_id, total in rows}
