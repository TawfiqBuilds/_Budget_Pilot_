import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user, CurrentUser
from app.db.session import get_db
from app.models.category import Category
from app.models.category_month import CategoryMonth
from app.models.purchase import Purchase

router = APIRouter(prefix="/account", tags=["account"])


class DeleteAccountRequest(BaseModel):
    confirm_email: str


@router.delete("", status_code=204)
def delete_account(
    body: DeleteAccountRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Deletes the user's account and every row of their data, permanently.

    The frontend disables the button until the typed text matches the user's
    email -- but that's just UX. The real check happens here: we compare the
    submitted email against the email in the verified JWT (not anything the
    client could fake), and only then run the cascade delete inside a single
    DB transaction. If any step fails, everything rolls back -- there is no
    state where the account is half-deleted.
    """
    if body.confirm_email.strip().lower() != (user.email or "").strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The email you typed doesn't match your account email.",
        )

    user_uuid = uuid.UUID(user.user_id)

    try:
        db.query(Purchase).filter(Purchase.user_id == user_uuid).delete()
        db.query(CategoryMonth).filter(CategoryMonth.user_id == user_uuid).delete()
        db.query(Category).filter(Category.user_id == user_uuid).delete()

        # Delete the Supabase auth user itself via the admin API. This uses the
        # service-role key, which must never be exposed to the frontend --
        # it only ever lives in this backend's environment variables.
        resp = httpx.delete(
            f"{settings.supabase_url}/auth/v1/admin/users/{user.user_id}",
            headers={
                "apikey": settings.supabase_service_role_key,
                "Authorization": f"Bearer {settings.supabase_service_role_key}",
            },
            timeout=10.0,
        )
        if resp.status_code not in (200, 204):
            raise RuntimeError(f"Supabase auth deletion failed: {resp.status_code} {resp.text}")

        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account deletion failed partway through. Nothing was deleted -- please try again.",
        )
