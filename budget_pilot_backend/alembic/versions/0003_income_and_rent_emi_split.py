"""add month_incomes table; split the combined Rent(incl. EMI) category

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-05

Two independent changes bundled together because they shipped together:

1. `month_incomes` -- one row per income source per month (salary, freelance,
   etc). A month's total income is just the sum of its rows. This is new
   infrastructure, so there's no backfill needed: existing months simply have
   zero income rows until the user adds some.

2. The old "Rent (incl. EMI)" fixed category mixed two very different
   expenses into one number. This migration, for every user who has that
   category:
     - renames it to "Rent" (its historical CategoryMonth/Purchase rows are
       untouched, so past months keep their numbers under the new name)
     - creates a new fixed "EMI" category right after it, seeded at 0 for
       every month "Rent (incl. EMI)" had a row for, so it shows up
       immediately in month history without guessing how much of the old
       combined number was EMI vs rent. The user re-enters the real EMI
       planned/actual amounts by hand for each month, since only they know
       the true split.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "month_incomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("month", sa.String(7), nullable=False, index=True),
        sa.Column("source", sa.String(120), nullable=False, server_default="Income"),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )

    bind = op.get_bind()

    # -- Data migration: split "Rent (incl. EMI)" into "Rent" + "EMI" --
    categories = sa.table(
        "categories",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("user_id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("type", sa.String),
        sa.column("is_default", sa.Boolean),
        sa.column("is_archived", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    category_months = sa.table(
        "category_months",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("user_id", postgresql.UUID(as_uuid=True)),
        sa.column("category_id", postgresql.UUID(as_uuid=True)),
        sa.column("month", sa.String),
        sa.column("planned_amount", sa.Numeric),
        sa.column("actual_amount", sa.Numeric),
        sa.column("notes", sa.Text),
    )

    old_rent_rows = bind.execute(
        sa.text("SELECT id, user_id, sort_order FROM categories WHERE name = :n AND is_default = true"),
        {"n": "Rent (incl. EMI)"},
    ).fetchall()

    for old_id, user_id, sort_order in old_rent_rows:
        # Rename in place -- this keeps every historical CategoryMonth /
        # Purchase row resolving correctly, since they point at category_id,
        # not the name.
        bind.execute(
            sa.text("UPDATE categories SET name = :new_name WHERE id = :id"),
            {"new_name": "Rent", "id": old_id},
        )

        import uuid
        new_emi_id = uuid.uuid4()
        bind.execute(
            sa.text(
                "INSERT INTO categories (id, user_id, name, type, is_default, is_archived, sort_order, created_at) "
                "VALUES (:id, :user_id, 'EMI', 'expense', true, false, :sort_order, now())"
            ),
            {"id": new_emi_id, "user_id": user_id, "sort_order": sort_order + 1},
        )

        months_with_rent = bind.execute(
            sa.text("SELECT DISTINCT month FROM category_months WHERE category_id = :cid"),
            {"cid": old_id},
        ).fetchall()
        for (month,) in months_with_rent:
            bind.execute(
                sa.text(
                    "INSERT INTO category_months (id, user_id, category_id, month, planned_amount, actual_amount, notes) "
                    "VALUES (:id, :user_id, :cid, :month, 0, 0, '') "
                    "ON CONFLICT (category_id, month) DO NOTHING"
                ),
                {"id": uuid.uuid4(), "user_id": user_id, "cid": new_emi_id, "month": month},
            )


def downgrade() -> None:
    op.drop_table("month_incomes")
    # The Rent/EMI split is not reversed automatically -- merging the numbers
    # back would require deciding how to recombine two now-independently-edited
    # categories, which isn't safe to do without user input.
