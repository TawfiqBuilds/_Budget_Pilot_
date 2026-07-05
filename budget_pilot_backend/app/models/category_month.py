import uuid

from sqlalchemy import String, Numeric, Text, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CategoryMonth(Base):
    """
    One row = "this category, this specific month". This is what makes history
    permanent: archiving a category never touches these rows. A month view is
    just "give me every CategoryMonth row where month = X", joined to whatever
    the category was called at the time.
    """

    __tablename__ = "category_months"
    __table_args__ = (UniqueConstraint("category_id", "month", name="uq_category_month"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Stored as "YYYY-MM" text to match the app's existing month-key format.
    month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    planned_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    actual_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
