import uuid

from pydantic import BaseModel


class MonthEntryOut(BaseModel):
    category_id: uuid.UUID
    category_name: str
    category_type: str
    is_default: bool
    is_archived: bool
    month: str
    planned_amount: float
    actual_amount: float
    notes: str


class MonthEntryUpsert(BaseModel):
    planned_amount: float | None = None
    actual_amount: float | None = None
    notes: str | None = None
