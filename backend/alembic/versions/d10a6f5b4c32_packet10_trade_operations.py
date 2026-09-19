"""Add provenance and pending trade storage requests for Packet 10.

Revision ID: d10a6f5b4c32
Revises: 9b8c7d6e5f4a
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d10a6f5b4c32"
down_revision = "9b8c7d6e5f4a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uid = postgresql.UUID(as_uuid=True)
    op.add_column("trade_events", sa.Column("source_kind", sa.Text(), nullable=True))
    op.add_column("trade_events", sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("trade_events", sa.Column("idempotency_key", sa.Text(), nullable=True))
    op.create_unique_constraint("uq_trade_event_idempotency_key", "trade_events", ["idempotency_key"])

    op.add_column(
        "payments",
        sa.Column("source_kind", sa.Text(), nullable=False, server_default="UNKNOWN_LEGACY"),
    )
    op.add_column("payments", sa.Column("reported_by_id", uid, sa.ForeignKey("users.id"), nullable=True))
    op.add_column("payments", sa.Column("idempotency_key", sa.Text(), nullable=True))
    op.create_unique_constraint("uq_payment_idempotency_key", "payments", ["idempotency_key"])

    op.add_column(
        "evidence",
        sa.Column("classification", sa.Text(), nullable=False, server_default="UNKNOWN_LEGACY"),
    )
    op.add_column(
        "evidence",
        sa.Column("provenance_status", sa.Text(), nullable=False, server_default="UNKNOWN_LEGACY"),
    )
    op.add_column("evidence", sa.Column("file_size_bytes", sa.Integer(), nullable=True))
    op.add_column("evidence", sa.Column("original_filename", sa.Text(), nullable=True))
    op.add_column(
        "storage_facilities",
        sa.Column("source_kind", sa.Text(), nullable=False, server_default="UNKNOWN_LEGACY"),
    )

    op.create_table(
        "trade_storage_requests",
        sa.Column("id", uid, primary_key=True),
        sa.Column("transaction_id", uid, sa.ForeignKey("transactions.id"), nullable=False),
        sa.Column("facility_id", uid, sa.ForeignKey("storage_facilities.id"), nullable=False),
        sa.Column("requested_by_id", uid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="REQUESTED"),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity > 0", name="ck_trade_storage_request_qty"),
        sa.CheckConstraint("status = 'REQUESTED'", name="ck_trade_storage_request_pending_only"),
        sa.UniqueConstraint("idempotency_key", name="uq_trade_storage_request_idempotency_key"),
    )
    op.create_index("ix_trade_storage_request_txn", "trade_storage_requests", ["transaction_id"])


def downgrade() -> None:
    op.drop_index("ix_trade_storage_request_txn", table_name="trade_storage_requests")
    op.drop_table("trade_storage_requests")
    op.drop_column("storage_facilities", "source_kind")
    op.drop_column("evidence", "original_filename")
    op.drop_column("evidence", "file_size_bytes")
    op.drop_column("evidence", "provenance_status")
    op.drop_column("evidence", "classification")
    op.drop_constraint("uq_payment_idempotency_key", "payments", type_="unique")
    op.drop_column("payments", "idempotency_key")
    op.drop_column("payments", "reported_by_id")
    op.drop_column("payments", "source_kind")
    op.drop_constraint("uq_trade_event_idempotency_key", "trade_events", type_="unique")
    op.drop_column("trade_events", "idempotency_key")
    op.drop_column("trade_events", "metadata")
    op.drop_column("trade_events", "source_kind")
