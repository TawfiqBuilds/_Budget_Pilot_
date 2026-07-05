"""drop reference_items -- superseded by purchases filtered by category

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-06

reference_items duplicated what purchases already does (and had a real bug:
it was never scoped to a month, so items 'in the same bucket' bled across
every month). "What's inside a bucket" is now just purchases filtered by
category_id + month, which is already correctly month-scoped.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

reference_bucket_enum = postgresql.ENUM("food", "personal", name="referencebucket")


def upgrade() -> None:
    op.drop_table("reference_items")
    bind = op.get_bind()
    reference_bucket_enum.drop(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    reference_bucket_enum.create(bind, checkfirst=True)
    op.create_table(
        "reference_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("bucket", reference_bucket_enum, nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
