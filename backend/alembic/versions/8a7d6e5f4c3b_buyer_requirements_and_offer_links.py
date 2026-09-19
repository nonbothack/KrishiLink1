"""Add buyer procurement quantities and explicit offer requirement links.

Revision ID: 8a7d6e5f4c3b
Revises: 73b4c9e10a62
"""

from alembic import op
import sqlalchemy as sa

revision = "8a7d6e5f4c3b"
down_revision = "73b4c9e10a62"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("buyer_requirements", sa.Column("requested_quantity", sa.Numeric(12, 3), nullable=True))
    op.add_column("buyer_requirements", sa.Column("requested_unit", sa.Text(), nullable=True))
    op.add_column("buyer_requirements", sa.Column("canonical_quantity", sa.Numeric(12, 2), nullable=True))
    op.add_column("buyer_requirements", sa.Column("committed_quantity", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("buyer_requirements", sa.Column("status", sa.Text(), nullable=False, server_default="DRAFT"))
    op.add_column("buyer_requirements", sa.Column("location_text", sa.Text(), nullable=True))
    op.add_column("buyer_requirements", sa.Column("allow_partial", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("buyer_requirements", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("buyer_requirements", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("offers", sa.Column("buyer_requirement_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_offers_buyer_requirement", "offers", "buyer_requirements", ["buyer_requirement_id"], ["id"])
    op.create_index("ix_offers_requirement", "offers", ["buyer_requirement_id"])


def downgrade() -> None:
    op.drop_index("ix_offers_requirement", table_name="offers")
    op.drop_constraint("fk_offers_buyer_requirement", "offers", type_="foreignkey")
    op.drop_column("offers", "buyer_requirement_id")
    for column in ("updated_at", "notes", "allow_partial", "location_text", "status", "committed_quantity", "canonical_quantity", "requested_unit", "requested_quantity"):
        op.drop_column("buyer_requirements", column)
