import uuid
import enum

from sqlalchemy import String, Boolean, Integer, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CategoryType(str, enum.Enum):
    expense = "expense"
    saving = "saving"


class Category(Base):
    """
    A category is created once and, in spirit, never deleted. Archiving
    (is_archived=True) removes it from "pick a category" pickers for new
    months/purchases, but every CategoryMonth / Purchase row that already
    points at this category.id keeps resolving correctly forever.

    The 8 fixed categories (is_default=True) cannot be archived or deleted
    at all -- only their per-month planned_amount can change. That rule is
    enforced in crud/category.py, not just in the frontend.
    """

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[CategoryType] = mapped_column(Enum(CategoryType), nullable=False, default=CategoryType.expense)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
