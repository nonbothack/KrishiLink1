"""Add explicitly scoped Web Push subscriptions and deduplicated delivery receipts.

Revision ID: d73f2c91a604
Revises: b611e2a7c930
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d73f2c91a604"
down_revision = "b611e2a7c930"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uid = postgresql.UUID(as_uuid=True)
    op.create_table(
        "web_push_subscriptions",
        sa.Column("id", uid, primary_key=True),
        sa.Column("user_id", uid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("endpoint_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("p256dh", sa.Text(), nullable=False),
        sa.Column("auth", sa.Text(), nullable=False),
        sa.Column("language", sa.Text(), nullable=False, server_default="en"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_web_push_subscription_user_active", "web_push_subscriptions", ["user_id", "is_active"])
    op.create_table(
        "web_push_deliveries",
        sa.Column("id", uid, primary_key=True),
        sa.Column("notification_id", uid, sa.ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subscription_id", uid, sa.ForeignKey("web_push_subscriptions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="PENDING"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_outcome", sa.Text(), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("notification_id", "subscription_id", name="uq_web_push_notification_subscription"),
    )
    op.create_index("ix_web_push_delivery_status_next", "web_push_deliveries", ["status", "next_attempt_at"])
    op.create_table(
        "web_push_attempts",
        sa.Column("id", uid, primary_key=True),
        sa.Column("delivery_id", uid, sa.ForeignKey("web_push_deliveries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("delivery_id", "attempt_number", name="uq_web_push_delivery_attempt_number"),
    )
    op.create_index("ix_web_push_attempted_at", "web_push_attempts", ["attempted_at"])


def downgrade() -> None:
    op.drop_index("ix_web_push_attempted_at", table_name="web_push_attempts")
    op.drop_table("web_push_attempts")
    op.drop_index("ix_web_push_delivery_status_next", table_name="web_push_deliveries")
    op.drop_table("web_push_deliveries")
    op.drop_index("ix_web_push_subscription_user_active", table_name="web_push_subscriptions")
    op.drop_table("web_push_subscriptions")
