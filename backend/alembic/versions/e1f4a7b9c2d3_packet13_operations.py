"""Add least-privilege staff operations and review records.

Revision ID: e1f4a7b9c2d3
Revises: d73f2c91a604
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e1f4a7b9c2d3"
down_revision = "d73f2c91a604"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uid = postgresql.UUID(as_uuid=True)
    op.add_column("users", sa.Column("account_status", sa.Text(), nullable=False, server_default="ACTIVE"))
    op.add_column("users", sa.Column("restricted_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("restriction_reason", sa.Text(), nullable=True))
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.create_check_constraint("ck_users_role", "users", "role IN ('farmer','buyer','fpo','admin','operator','support','reviewer','fraud_reviewer')")
    op.add_column("outbox_events", sa.Column("correlation_id", sa.Text(), nullable=True))
    op.add_column("outbox_events", sa.Column("last_error_category", sa.Text(), nullable=True))
    op.add_column("outbox_events", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_outbox_events_correlation_id", "outbox_events", ["correlation_id"])
    op.create_table(
        "staff_action_grants",
        sa.Column("id", uid, primary_key=True),
        sa.Column("staff_user_id", uid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.Text(), nullable=True),
        sa.Column("action_family", sa.Text(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_staff_action_grants_staff_user_id", "staff_action_grants", ["staff_user_id"])
    op.create_index("ix_staff_action_grants_session_id", "staff_action_grants", ["session_id"])
    op.create_table(
        "fraud_cases",
        sa.Column("id", uid, primary_key=True), sa.Column("subject_type", sa.Text(), nullable=False),
        sa.Column("subject_id", sa.Text(), nullable=False), sa.Column("signal_type", sa.Text(), nullable=False),
        sa.Column("rule_id", sa.Text(), nullable=False), sa.Column("rule_version", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False, server_default="LOW"), sa.Column("evidence_refs", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("status", sa.Text(), nullable=False, server_default="OPEN"), sa.Column("assigned_reviewer_id", uid, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("decision", sa.Text(), nullable=True), sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("subject_type", "subject_id", "signal_type", "rule_version", name="uq_fraud_case_signal"),
    )
    op.create_index("ix_fraud_cases_subject_id", "fraud_cases", ["subject_id"])
    op.create_table(
        "support_cases",
        sa.Column("id", uid, primary_key=True), sa.Column("public_reference", sa.Text(), nullable=False, unique=True),
        sa.Column("requester_id", uid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("category", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("linked_grievance_id", uid, sa.ForeignKey("disputes.id"), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="OPEN"), sa.Column("assigned_staff_id", uid, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_support_cases_requester_id", "support_cases", ["requester_id"])
    op.create_table(
        "support_notes",
        sa.Column("id", uid, primary_key=True), sa.Column("case_id", uid, sa.ForeignKey("support_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", uid, sa.ForeignKey("users.id"), nullable=False), sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_support_notes_case_id", "support_notes", ["case_id"])
    op.create_table(
        "incident_records",
        sa.Column("id", uid, primary_key=True), sa.Column("title", sa.Text(), nullable=False), sa.Column("severity", sa.Text(), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.Text(), nullable=False, server_default="OPEN"), sa.Column("affected_capability", sa.Text(), nullable=True), sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("runbook_ref", sa.Text(), nullable=True), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True), sa.Column("created_by", uid, sa.ForeignKey("users.id"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("incident_records")
    op.drop_index("ix_support_notes_case_id", table_name="support_notes")
    op.drop_table("support_notes")
    op.drop_index("ix_support_cases_requester_id", table_name="support_cases")
    op.drop_table("support_cases")
    op.drop_index("ix_fraud_cases_subject_id", table_name="fraud_cases")
    op.drop_table("fraud_cases")
    op.drop_index("ix_staff_action_grants_session_id", table_name="staff_action_grants")
    op.drop_index("ix_staff_action_grants_staff_user_id", table_name="staff_action_grants")
    op.drop_table("staff_action_grants")
    op.drop_index("ix_outbox_events_correlation_id", table_name="outbox_events")
    op.drop_column("outbox_events", "processed_at")
    op.drop_column("outbox_events", "last_error_category")
    op.drop_column("outbox_events", "correlation_id")
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.create_check_constraint("ck_users_role", "users", "role IN ('farmer','buyer','fpo','admin','operator')")
    op.drop_column("users", "restriction_reason")
    op.drop_column("users", "restricted_until")
    op.drop_column("users", "account_status")
