import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category, CategoryType

DEFAULT_CATEGORIES = [
    ("Rent", CategoryType.expense),
    ("EMI", CategoryType.expense),
    ("Food bucket", CategoryType.expense),
    ("Personal bucket", CategoryType.expense),
    
   
    ("Charity", CategoryType.expense),
    ("Upskilling", CategoryType.expense),
    ("Entertainment", CategoryType.expense),
]


def seed_default_categories(db: Session, user_id: uuid.UUID) -> list[Category]:
    """Called once, right after signup. Creates the 8 fixed categories for this user."""
    existing = db.scalar(select(Category).where(Category.user_id == user_id).limit(1))
    if existing:
        return list(db.scalars(select(Category).where(Category.user_id == user_id)))

    rows = [
        Category(user_id=user_id, name=name, type=ctype, is_default=True, sort_order=i)
        for i, (name, ctype) in enumerate(DEFAULT_CATEGORIES)
    ]
    db.add_all(rows)
    db.commit()
    for r in rows:
        db.refresh(r)
    return rows


def list_categories(db: Session, user_id: uuid.UUID, include_archived: bool = False) -> list[Category]:
    stmt = select(Category).where(Category.user_id == user_id)
    if not include_archived:
        stmt = stmt.where(Category.is_archived.is_(False))
    stmt = stmt.order_by(Category.sort_order, Category.created_at)
    return list(db.scalars(stmt))


def get_category_or_404(db: Session, user_id: uuid.UUID, category_id: uuid.UUID) -> Category:
    cat = db.scalar(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    )
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    return cat


def create_category(db: Session, user_id: uuid.UUID, name: str, type_: CategoryType) -> Category:
    max_order = db.scalar(select(Category.sort_order).where(Category.user_id == user_id).order_by(Category.sort_order.desc()).limit(1))
    cat = Category(user_id=user_id, name=name.strip(), type=type_, is_default=False, sort_order=(max_order or 0) + 1)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def rename_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID, new_name: str) -> Category:
    cat = get_category_or_404(db, user_id, category_id)
    cat.name = new_name.strip()
    db.commit()
    db.refresh(cat)
    return cat


def archive_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID) -> Category:
    cat = get_category_or_404(db, user_id, category_id)
    if cat.is_default:
        # Server-side enforcement of decision #1: the 8 fixed categories are
        # permanent. This check exists here, not just in the React UI, because
        # a request straight to the API must be blocked too.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This is one of your fixed categories and can't be archived. You can still edit its planned amount.",
        )
    cat.is_archived = True
    db.commit()
    db.refresh(cat)
    return cat


def restore_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID) -> Category:
    cat = get_category_or_404(db, user_id, category_id)
    cat.is_archived = False
    db.commit()
    db.refresh(cat)
    return cat


def hard_delete_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID, cascade: bool) -> None:
    from app.models.category_month import CategoryMonth
    from app.models.purchase import Purchase

    cat = get_category_or_404(db, user_id, category_id)
    if cat.is_default:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fixed categories can never be deleted.")

    has_history = db.scalar(
        select(CategoryMonth.id).where(CategoryMonth.category_id == category_id).limit(1)
    ) or db.scalar(select(Purchase.id).where(Purchase.category_id == category_id).limit(1))

    if has_history and not cascade:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This category has historical data. Archive it instead, or pass ?cascade=true to delete everything permanently.",
        )

    if has_history and cascade:
        db.query(Purchase).filter(Purchase.category_id == category_id).delete()
        db.query(CategoryMonth).filter(CategoryMonth.category_id == category_id).delete()

    db.delete(cat)
    db.commit()
