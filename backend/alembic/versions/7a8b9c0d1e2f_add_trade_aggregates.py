"""add_trade_aggregates

Revision ID: 7a8b9c0d1e2f
Revises: 6442a44b1f27
Create Date: 2026-09-01 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, Sequence[str], None] = '6442a44b1f27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    uuid_type = postgresql.UUID(as_uuid=True) if bind.dialect.name == "postgresql" else sa.CHAR(32)

    # 1. Add public_id to transactions
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.add_column(sa.Column("public_id", sa.Text(), nullable=True))
        batch_op.create_unique_constraint("uq_transactions_public_id", ["public_id"])
        batch_op.create_index("ix_txn_public_id", ["public_id"])

    # 2. Create trade_term_snapshots
    op.create_table(
        "trade_term_snapshots",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("transaction_id", uuid_type, sa.ForeignKey("transactions.id"), nullable=False, unique=True),
        sa.Column("lot_id", uuid_type, sa.ForeignKey("lots.id"), nullable=False),
        sa.Column("buyer_id", uuid_type, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("seller_id", uuid_type, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("crop_name", sa.Text(), nullable=False),
        sa.Column("grade", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit", sa.Text(), server_default="quintal", nullable=False),
        sa.Column("price_per_unit", sa.Numeric(12, 2), nullable=False),
        sa.Column("gross_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("estimated_net_realization", sa.Numeric(12, 2), nullable=True),
        sa.Column("delivery_window", sa.Text(), nullable=True),
        sa.Column("pickup_location", sa.Text(), nullable=True),
        sa.Column("delivery_location", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trade_terms_txn", "trade_term_snapshots", ["transaction_id"])

    # 3. Create trade_events
    op.create_table(
        "trade_events",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("transaction_id", uuid_type, sa.ForeignKey("transactions.id"), nullable=False),
        sa.Column("actor_id", uuid_type, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("actor_role", sa.Text(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("from_status", sa.Text(), nullable=True),
        sa.Column("to_status", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trade_events_txn", "trade_events", ["transaction_id"])
    op.create_index("ix_trade_events_created", "trade_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("trade_events")
    op.drop_table("trade_term_snapshots")
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_index("ix_txn_public_id")
        batch_op.drop_constraint("uq_transactions_public_id", type_="unique")
        batch_op.drop_column("public_id")
