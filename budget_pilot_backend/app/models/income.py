import uuid

from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MonthIncome(Base):
    """
    One row = one income source, for one specific month (e.g. "Salary - 45632"
    for 2026-07, plus a separate "Freelance - 8000" row for the same month).
    A month's total income is just the sum of every row for that month --
    this is what lets "multiple income sources, entered manually every month"
    work without inventing a separate recurring-income concept.
    """

    __tablename__ = "month_incomes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    # Stored as "YYYY-MM" text, same convention as CategoryMonth.month.
    month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False, default="Income")
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
