import uuid

from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session

from app.core.security import get_current_user, CurrentUser
from app.db.session import get_db
from app.schemas.purchase import PurchaseOut, PurchaseCreate
from app.crud import purchase as crud_purchase

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.get("", response_model=list[PurchaseOut])
def list_purchases(
    month: str | None = Query(None, description="Filter to a 'YYYY-MM' month"),
    category_id: uuid.UUID | None = Query(None, description="Filter to purchases in one category"),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return crud_purchase.list_purchases(db, uuid.UUID(user.user_id), month, category_id)


@router.post("", response_model=PurchaseOut, status_code=201)
def create_purchase(
    body: PurchaseCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return crud_purchase.create_purchase(db, uuid.UUID(user.user_id), body.category_id, body.name, body.amount, body.date)


@router.delete("/{purchase_id}", status_code=204)
def delete_purchase(
    purchase_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    crud_purchase.delete_purchase(db, uuid.UUID(user.user_id), purchase_id)
