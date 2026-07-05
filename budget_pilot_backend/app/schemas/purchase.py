import uuid
import datetime

from pydantic import BaseModel, ConfigDict


class PurchaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    name: str
    amount: float
    date: datetime.datetime


class PurchaseCreate(BaseModel):
    category_id: uuid.UUID
    name: str
    amount: float
    date: datetime.datetime | None = None
