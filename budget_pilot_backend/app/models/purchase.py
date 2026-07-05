import uuid

from sqlalchemy import String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Purchase(Base):
    """
    A single logged purchase (e.g. "Badam 500g - Rs 270"). Unlike categories,
    individual purchases genuinely can be hard-deleted -- deleting one receipt
    doesn't erase a whole category's history, so there's no "everything vanished"
    risk here.
    """

    __tablename__ = "purchases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    date: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
