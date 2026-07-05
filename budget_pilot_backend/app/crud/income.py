import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.income import MonthIncome


def list_income(db: Session, user_id: uuid.UUID, month: str) -> list[MonthIncome]:
    stmt = (
        select(MonthIncome)
        .where(MonthIncome.user_id == user_id, MonthIncome.month == month)
        .order_by(MonthIncome.source)
    )
    return list(db.scalars(stmt))


def total_income(db: Session, user_id: uuid.UUID, month: str) -> float:
    return sum(float(row.amount) for row in list_income(db, user_id, month))


def add_income(db: Session, user_id: uuid.UUID, month: str, source: str, amount: float) -> MonthIncome:
    row = MonthIncome(user_id=user_id, month=month, source=(source or "Income").strip() or "Income", amount=amount)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_income(
    db: Session,
    user_id: uuid.UUID,
    income_id: uuid.UUID,
    source: str | None = None,
    amount: float | None = None,
) -> MonthIncome:
    row = db.scalar(select(MonthIncome).where(MonthIncome.id == income_id, MonthIncome.user_id == user_id))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income source not found.")
    if source is not None:
        row.source = source.strip() or "Income"
    if amount is not None:
        row.amount = amount
    db.commit()
    db.refresh(row)
    return row


def delete_income(db: Session, user_id: uuid.UUID, income_id: uuid.UUID) -> None:
    row = db.scalar(select(MonthIncome).where(MonthIncome.id == income_id, MonthIncome.user_id == user_id))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income source not found.")
    db.delete(row)
    db.commit()
