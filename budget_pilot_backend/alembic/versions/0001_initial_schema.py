"""initial schema: categories, category_months, purchases, reference_items

Revision ID: 0001
Revises:
Create Date: 2026-07-04

This migration creates the new relational schema alongside the existing
`ledger_data` blob table. `ledger_data` is NOT touched or dropped here --
see scripts/migrate_from_blob.py for moving data across, and the plan doc's
"Migration plan" section for why we keep ledger_data as a cold backup during
the cutover.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

category_type_enum = postgresql.ENUM("expense", "saving", name="categorytype")
reference_bucket_enum = postgresql.ENUM("food", "personal", name="referencebucket")


def upgrade() -> None:
    bind = op.get_bind()
    category_type_enum.create(bind, checkfirst=True)
    reference_bucket_enum.create(bind, checkfirst=True)

    # We just created these types by hand above. Without this, SQLAlchemy tries
    # to CREATE TYPE again as a side effect of create_table() below, which fails
    # with "type already exists" since it doesn't track that we made it manually.
    category_type_enum.create_type = False
    reference_bucket_enum.create_type = False

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("type", category_type_enum, nullable=False, server_default="expense"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "category_months",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categories.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("month", sa.String(7), nullable=False, index=True),
        sa.Column("planned_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("actual_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint("category_id", "month", name="uq_category_month"),
    )

    op.create_table(
        "purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categories.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "reference_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("bucket", reference_bucket_enum, nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("reference_items")
    op.drop_table("purchases")
    op.drop_table("category_months")
    op.drop_table("categories")
    bind = op.get_bind()
    reference_bucket_enum.drop(bind, checkfirst=True)
    category_type_enum.drop(bind, checkfirst=True)
