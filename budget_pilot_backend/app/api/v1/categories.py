import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user, CurrentUser
from app.db.session import get_db
from app.schemas.category import CategoryOut, CategoryCreate, CategoryRename
from app.crud import category as crud_category

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    # First time this user has ever hit this endpoint -> seed_default_categories
    # is a no-op after the first call (it checks for existing rows first), so
    # this is safe to call on every request.
    crud_category.seed_default_categories(db, uuid.UUID(user.user_id))
    return crud_category.list_categories(db, uuid.UUID(user.user_id), include_archived)


@router.get("/archived", response_model=list[CategoryOut])
def list_archived_categories(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Every archived category, regardless of month -- including ones archived
    with no data at all, which never show up in any /months/{month} view and
    would otherwise be permanently unreachable (no Restore button anywhere).
    """
    from app.crud import category_month as crud_month
    return crud_month.list_all_archived(db, uuid.UUID(user.user_id))


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(
    body: CategoryCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return crud_category.create_category(db, uuid.UUID(user.user_id), body.name, body.type)


@router.patch("/{category_id}", response_model=CategoryOut)
def rename_category(
    category_id: uuid.UUID,
    body: CategoryRename,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return crud_category.rename_category(db, uuid.UUID(user.user_id), category_id, body.name)


@router.post("/{category_id}/archive", response_model=CategoryOut)
def archive_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    # Fixed-category protection is enforced inside crud_category.archive_category,
    # not here -- so a direct API call can't bypass it either.
    return crud_category.archive_category(db, uuid.UUID(user.user_id), category_id)


@router.post("/{category_id}/restore", response_model=CategoryOut)
def restore_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return crud_category.restore_category(db, uuid.UUID(user.user_id), category_id)


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: uuid.UUID,
    cascade: bool = Query(False, description="Permanently delete all history for this category too."),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    crud_category.hard_delete_category(db, uuid.UUID(user.user_id), category_id, cascade)
