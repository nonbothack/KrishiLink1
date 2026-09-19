"""Add evidence-linked reported-price alert rules and evaluation receipts.

Revision ID: b611e2a7c930
Revises: d10a6f5b4c32
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b611e2a7c930"
down_revision = "d10a6f5b4c32"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uid = postgresql.UUID(as_uuid=True)
    op.add_column("notifications", sa.Column("metadata", sa.JSON(), nullable=True))
    op.create_table(
        "price_alert_rules",
        sa.Column("id", uid, primary_key=True),
        sa.Column("user_id", uid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crop_id", uid, sa.ForeignKey("crops.id"), nullable=False),
        sa.Column("market_id", uid, sa.ForeignKey("markets.id"), nullable=False),
        sa.Column("variety_id", uid, sa.ForeignKey("crop_varieties.id"), nullable=True),
        sa.Column("grade", sa.Text(), nullable=True),
        sa.Column("threshold", sa.Numeric(12, 2), nullable=False),
        sa.Column("direction", sa.Text(), nullable=False),
        sa.Column("price_unit", sa.Text(), nullable=False, server_default="INR/quintal"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_armed", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("threshold > 0", name="ck_price_alert_threshold_positive"),
        sa.CheckConstraint("direction IN ('AT_OR_ABOVE','AT_OR_BELOW')", name="ck_price_alert_direction"),
        sa.CheckConstraint("price_unit = 'INR/quintal'", name="ck_price_alert_unit"),
    )
    op.create_index("ix_price_alert_user_active", "price_alert_rules", ["user_id", "is_active"])
    op.create_table(
        "price_alert_evaluations",
        sa.Column("id", uid, primary_key=True),
        sa.Column("alert_id", uid, sa.ForeignKey("price_alert_rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("observation_id", uid, sa.ForeignKey("price_observations.id"), nullable=False),
        sa.Column("triggered", sa.Boolean(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("alert_id", "observation_id", name="uq_price_alert_observation"),
    )
    op.create_index("ix_price_alert_eval_alert", "price_alert_evaluations", ["alert_id", "evaluated_at"])


def downgrade() -> None:
    op.drop_index("ix_price_alert_eval_alert", table_name="price_alert_evaluations")
    op.drop_table("price_alert_evaluations")
    op.drop_index("ix_price_alert_user_active", table_name="price_alert_rules")
    op.drop_table("price_alert_rules")
    op.drop_column("notifications", "metadata")
