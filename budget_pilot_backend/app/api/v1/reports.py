import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user, CurrentUser
from app.db.session import get_db
from app.services import budget_calc

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/history")
def get_history(
    end_month: str = Query(..., description="Last month in the range, 'YYYY-MM'"),
    months: int = Query(12, ge=1, le=36),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return budget_calc.get_history(db, uuid.UUID(user.user_id), end_month, months)


@router.get("/savings-lifetime")
def get_savings_lifetime(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return budget_calc.get_savings_lifetime(db, uuid.UUID(user.user_id))
