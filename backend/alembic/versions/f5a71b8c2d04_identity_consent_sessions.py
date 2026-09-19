"""Add identity, OTP, refresh-session, verification and consent foundations.

Revision ID: f5a71b8c2d04
Revises: e47b91c6a2d0
Create Date: 2026-09-17
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f5a71b8c2d04"
down_revision: Union[str, Sequence[str], None] = "e47b91c6a2d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _canonical_phone(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"[\s().-]", "", value.strip())
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]
    if not re.fullmatch(r"[6-9][0-9]{9}", cleaned):
        return None
    return f"+91{cleaned}"


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("phone_canonical", sa.Text(), nullable=True))
        batch.add_column(sa.Column("auth_token_version", sa.Integer(), server_default="0", nullable=False))
        batch.add_column(sa.Column("identity_review_required", sa.Boolean(), server_default=sa.false(), nullable=False))
        batch.add_column(sa.Column("phone_verified_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("coordinate_accuracy_m", sa.Numeric(10, 2), nullable=True))
        batch.create_unique_constraint("uq_users_phone_canonical", ["phone_canonical"])

    with op.batch_alter_table("buyer_profiles") as batch:
        batch.add_column(
            sa.Column("business_verification_status", sa.Text(), server_default="UNVERIFIED", nullable=False)
        )
    with op.batch_alter_table("fpo_profiles") as batch:
        batch.add_column(
            sa.Column("organization_verification_status", sa.Text(), server_default="UNVERIFIED", nullable=False)
        )

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("family_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
    )
    op.create_index("ix_auth_sessions_family_id", "auth_sessions", ["family_id"])
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])

    op.create_table(
        "otp_challenges",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("phone_hash", sa.Text(), nullable=False),
        sa.Column("code_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_ip_hash", sa.Text(), nullable=True),
        sa.Column("delivery_provider", sa.Text(), nullable=True),
    )
    op.create_index("ix_otp_challenges_phone_hash", "otp_challenges", ["phone_hash"])
    op.create_index("ix_otp_phone_created", "otp_challenges", ["phone_hash", "created_at"])

    op.create_table(
        "phone_identity_conflicts",
        sa.Column("canonical_phone", sa.Text(), primary_key=True),
        sa.Column("legacy_user_ids", sa.JSON(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolution_status", sa.Text(), server_default="needs_review", nullable=False),
    )

    op.create_table(
        "consent_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_type", sa.Text(), nullable=False),
        sa.Column("policy_version", sa.Text(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.Text(), server_default="web_registration", nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "policy_type IN ('terms','privacy_notice','marketing','location_gps')",
            name="ck_consent_policy_type",
        ),
    )
    op.create_index("ix_consent_records_user_id", "consent_records", ["user_id"])
    op.create_index(
        "ix_consent_user_policy_accepted", "consent_records", ["user_id", "policy_type", "accepted_at"]
    )

    op.create_table(
        "verification_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dimension", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default="UNVERIFIED", nullable=False),
        sa.Column("method", sa.Text(), nullable=True),
        sa.Column("provider", sa.Text(), nullable=True),
        sa.Column("provider_reference", sa.Text(), nullable=True),
        sa.Column("reason_code", sa.Text(), nullable=True),
        sa.Column("evidence_metadata", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "dimension IN ('phone','email','identity','business','gst','bank','organization')",
            name="ck_verification_dimension",
        ),
        sa.CheckConstraint(
            "status IN ('UNVERIFIED','PENDING_REVIEW','VERIFIED','REJECTED','NEEDS_MORE_INFORMATION','UNAVAILABLE')",
            name="ck_verification_status",
        ),
    )
    op.create_index("ix_verification_records_user_id", "verification_records", ["user_id"])
    op.create_index(
        "ix_verification_user_dimension_created", "verification_records", ["user_id", "dimension", "created_at"]
    )

    op.create_table(
        "password_reset_grants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_password_reset_grants_user_id", "password_reset_grants", ["user_id"])

    op.create_table(
        "privacy_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default="RECEIVED", nullable=False),
        sa.Column("user_note", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("request_type IN ('access','correction','erasure')", name="ck_privacy_request_type"),
        sa.CheckConstraint("status IN ('RECEIVED','IN_REVIEW','COMPLETED','DECLINED')", name="ck_privacy_request_status"),
    )
    op.create_index("ix_privacy_requests_user_id", "privacy_requests", ["user_id"])

    # Populate canonical keys only for unambiguous existing identities. Never merge or rewrite a legacy account.
    connection = op.get_bind()
    grouped: dict[str, list[str]] = defaultdict(list)
    users: list[tuple[str, str | None]] = []
    for row in connection.execute(sa.text("SELECT id, phone FROM users WHERE phone IS NOT NULL")):
        user_id, raw_phone = str(row[0]), row[1]
        users.append((user_id, raw_phone))
        canonical = _canonical_phone(raw_phone)
        if canonical:
            grouped[canonical].append(user_id)
        else:
            connection.execute(
                sa.text("UPDATE users SET identity_review_required = true WHERE id = :user_id"),
                {"user_id": row[0]},
            )

    conflict_table = sa.table(
        "phone_identity_conflicts",
        sa.column("canonical_phone", sa.Text()),
        sa.column("legacy_user_ids", sa.JSON()),
        sa.column("resolution_status", sa.Text()),
    )
    for canonical, user_ids in grouped.items():
        if len(user_ids) > 1:
            for user_id in user_ids:
                connection.execute(
                    sa.text("UPDATE users SET identity_review_required = true WHERE id = :user_id"),
                    {"user_id": user_id},
                )
            connection.execute(
                sa.insert(conflict_table).values(
                    canonical_phone=canonical,
                    legacy_user_ids=user_ids,
                    resolution_status="needs_review",
                )
            )
        else:
            connection.execute(
                sa.text("UPDATE users SET phone_canonical = :canonical WHERE id = :user_id"),
                {"canonical": canonical, "user_id": user_ids[0]},
            )


def downgrade() -> None:
    connection = op.get_bind()
    protected_tables = (
        "auth_sessions",
        "otp_challenges",
        "phone_identity_conflicts",
        "consent_records",
        "verification_records",
        "password_reset_grants",
        "privacy_requests",
    )
    for table_name in protected_tables:
        count = connection.execute(sa.text(f"SELECT count(*) FROM {table_name}")).scalar_one()
        if count:
            raise RuntimeError(f"Refusing to drop {count} identity evidence rows from {table_name} during downgrade")

    for index in ("ix_privacy_requests_user_id", "ix_password_reset_grants_user_id"):
        table = "privacy_requests" if index.startswith("ix_privacy") else "password_reset_grants"
        op.drop_index(index, table_name=table)
    op.drop_table("privacy_requests")
    op.drop_table("password_reset_grants")
    op.drop_index("ix_verification_user_dimension_created", table_name="verification_records")
    op.drop_index("ix_verification_records_user_id", table_name="verification_records")
    op.drop_table("verification_records")
    op.drop_index("ix_consent_user_policy_accepted", table_name="consent_records")
    op.drop_index("ix_consent_records_user_id", table_name="consent_records")
    op.drop_table("consent_records")
    op.drop_table("phone_identity_conflicts")
    op.drop_index("ix_otp_phone_created", table_name="otp_challenges")
    op.drop_index("ix_otp_challenges_phone_hash", table_name="otp_challenges")
    op.drop_table("otp_challenges")
    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_family_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")

    with op.batch_alter_table("fpo_profiles") as batch:
        batch.drop_column("organization_verification_status")
    with op.batch_alter_table("buyer_profiles") as batch:
        batch.drop_column("business_verification_status")
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("uq_users_phone_canonical", type_="unique")
        batch.drop_column("coordinate_accuracy_m")
        batch.drop_column("email_verified_at")
        batch.drop_column("phone_verified_at")
        batch.drop_column("identity_review_required")
        batch.drop_column("auth_token_version")
        batch.drop_column("phone_canonical")
