import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user, CurrentUser
from app.db.session import get_db
from app.schemas.income import IncomeOut, IncomeCreate, IncomeUpdate
from app.crud import income as crud_income

router = APIRouter(prefix="/months", tags=["income"])


@router.get("/{month}/income", response_model=list[IncomeOut])
def list_income(
    month: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return crud_income.list_income(db, uuid.UUID(user.user_id), month)


@router.post("/{month}/income", response_model=IncomeOut, status_code=201)
def add_income(
    month: str,
    body: IncomeCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return crud_income.add_income(db, uuid.UUID(user.user_id), month, body.source, body.amount)


@router.patch("/income/{income_id}", response_model=IncomeOut)
def update_income(
    income_id: uuid.UUID,
    body: IncomeUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return crud_income.update_income(db, uuid.UUID(user.user_id), income_id, body.source, body.amount)


@router.delete("/income/{income_id}", status_code=204)
def delete_income(
    income_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    crud_income.delete_income(db, uuid.UUID(user.user_id), income_id)
