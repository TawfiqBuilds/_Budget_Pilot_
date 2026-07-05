import uuid

from pydantic import BaseModel, ConfigDict


class IncomeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    month: str
    source: str
    amount: float


class IncomeCreate(BaseModel):
    source: str = "Income"
    amount: float


class IncomeUpdate(BaseModel):
    source: str | None = None
    amount: float | None = None
