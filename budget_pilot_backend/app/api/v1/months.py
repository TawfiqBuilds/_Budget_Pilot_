import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user, CurrentUser
from app.db.session import get_db
from pydantic import BaseModel

from app.schemas.category_month import MonthEntryOut, MonthEntryUpsert
from app.crud import category_month as crud_month
from app.services import budget_calc

router = APIRouter(prefix="/months", tags=["months"])


class PushLeftoverRequest(BaseModel):
    savings_category_id: uuid.UUID


@router.get("/{month}/summary")
def get_month_summary(
    month: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return budget_calc.get_month_summary(db, uuid.UUID(user.user_id), month)


@router.get("/{month}", response_model=list[MonthEntryOut])
def get_month(
    month: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    rows = crud_month.get_month(db, uuid.UUID(user.user_id), month)
    return [MonthEntryOut(**row) for row in rows]


@router.put("/{month}/{category_id}", response_model=MonthEntryOut)
def upsert_month_entry(
    month: str,
    category_id: uuid.UUID,
    body: MonthEntryUpsert,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    row = crud_month.upsert_month_entry(
        db,
        uuid.UUID(user.user_id),
        category_id,
        month,
        planned_amount=body.planned_amount,
        actual_amount=body.actual_amount,
        notes=body.notes,
    )
    cat = row.__dict__.get("category")  # not eagerly loaded; fetch name separately below
    from app.crud.category import get_category_or_404
    cat = get_category_or_404(db, uuid.UUID(user.user_id), category_id)
    return MonthEntryOut(
        category_id=row.category_id,
        category_name=cat.name,
        category_type=cat.type.value,
        is_default=cat.is_default,
        is_archived=cat.is_archived,
        month=row.month,
        planned_amount=float(row.planned_amount),
        actual_amount=float(row.actual_amount),
        notes=row.notes,
    )


@router.post("/{month}/push-leftover", response_model=MonthEntryOut)
def push_leftover_to_savings(
    month: str,
    body: PushLeftoverRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Explicit, one-click version of "money I didn't use this month goes to
    savings": computes this month's leftover (income minus everything actually
    spent) and adds it on top of whatever is already logged as actual_amount
    for the chosen savings category (e.g. Emergency Fund). Deliberately a
    manual action rather than something that happens silently at month-end,
    so the number always matches something the user chose to do.
    """
    from app.crud.category import get_category_or_404

    user_uuid = uuid.UUID(user.user_id)
    summary = budget_calc.get_month_summary(db, user_uuid, month, include_prev=False)
    leftover = summary["leftover_amount"]
    if leftover <= 0:
        raise HTTPException(status_code=400, detail="There's no leftover this month to push to savings.")

    cat = get_category_or_404(db, user_uuid, body.savings_category_id)
    if cat.type.value != "saving":
        raise HTTPException(status_code=400, detail="Pick one of your saving-type categories for this.")

    existing_rows = crud_month.get_month(db, user_uuid, month)
    current = next((r["actual_amount"] for r in existing_rows if r["category_id"] == cat.id), 0.0)

    row = crud_month.upsert_month_entry(
        db, user_uuid, cat.id, month, actual_amount=round(current + leftover, 2)
    )
    return MonthEntryOut(
        category_id=row.category_id,
        category_name=cat.name,
        category_type=cat.type.value,
        is_default=cat.is_default,
        is_archived=cat.is_archived,
        month=row.month,
        planned_amount=float(row.planned_amount),
        actual_amount=float(row.actual_amount),
        notes=row.notes,
    )


@router.post("/{to_month}/clone-from/{from_month}", response_model=list[MonthEntryOut])
def clone_month(
    to_month: str,
    from_month: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    crud_month.clone_previous_month(db, uuid.UUID(user.user_id), from_month, to_month)
    return get_month(to_month, db, user)
