import uuid
import datetime

from pydantic import BaseModel, ConfigDict

from app.models.category import CategoryType


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: CategoryType
    is_default: bool
    is_archived: bool
    sort_order: int
    created_at: datetime.datetime


class CategoryCreate(BaseModel):
    name: str
    type: CategoryType = CategoryType.expense


class CategoryRename(BaseModel):
    name: str
