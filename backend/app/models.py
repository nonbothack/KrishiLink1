import uuid

from geoalchemy2 import Geography
from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    event,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class State(Base):
    __tablename__ = "geo_states"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lgd_code = Column(Text, unique=True, nullable=True)
    name = Column(Text, nullable=False)
    name_hindi = Column(Text, nullable=True)
    name_marathi = Column(Text, nullable=True)
    source_ref = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


class District(Base):
    __tablename__ = "geo_districts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state_id = Column(UUID(as_uuid=True), ForeignKey("geo_states.id"), nullable=False)
    lgd_code = Column(Text, unique=True, nullable=True)
    name = Column(Text, nullable=False)
    name_hindi = Column(Text, nullable=True)
    name_marathi = Column(Text, nullable=True)
    source_ref = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (UniqueConstraint("state_id", "name", name="uq_geo_district_state_name"),)


class Subdistrict(Base):
    __tablename__ = "geo_subdistricts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    district_id = Column(UUID(as_uuid=True), ForeignKey("geo_districts.id"), nullable=False)
    lgd_code = Column(Text, unique=True, nullable=True)
    name = Column(Text, nullable=False)
    name_hindi = Column(Text, nullable=True)
    name_marathi = Column(Text, nullable=True)
    source_ref = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (UniqueConstraint("district_id", "name", name="uq_geo_subdistrict_district_name"),)


class DataSourceRegistry(Base):
    __tablename__ = "data_source_registry"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_key = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    owner = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    license_name = Column(Text, nullable=True)
    license_url = Column(Text, nullable=True)
    license_status = Column(Text, nullable=False, default="unknown")
    retrieval_method = Column(Text, nullable=True)
    schema_version = Column(Text, nullable=True)
    expected_cadence = Column(Text, nullable=True)
    geographic_coverage = Column(Text, nullable=True)
    dedupe_key = Column(Text, nullable=True)
    parser_version = Column(Text, nullable=True)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    last_failure_at = Column(DateTime(timezone=True), nullable=True)
    freshness_sla_seconds = Column(Integer, nullable=True)
    unit_conventions = Column(JSON, nullable=False, default=dict)
    known_gaps = Column(JSON, nullable=False, default=list)
    last_run_status = Column(Text, nullable=True)
    last_run_counts = Column(JSON, nullable=True)
    quality_score = Column(Numeric(4, 3), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (
        CheckConstraint("license_status IN ('approved','restricted','unknown','not_applicable')", name="ck_data_source_license_status"),
    )


class SystemConfiguration(Base):
    __tablename__ = "system_configurations"
    key = Column(Text, primary_key=True)
    value = Column(JSONB, nullable=False)
    version = Column(Integer, server_default="1", nullable=False)
    updated_by = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(Text, nullable=True)
    action = Column(Text, nullable=False)
    entity = Column(Text, nullable=False)
    entity_id = Column(Text, nullable=True)
    before = Column(JSONB, nullable=True)
    after = Column(JSONB, nullable=True)
    request_id = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate = Column(Text, nullable=False)
    aggregate_id = Column(Text, nullable=False)
    event_type = Column(Text, nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(Text, server_default="PENDING", nullable=False)
    retry_count = Column(Integer, server_default="0", nullable=False)
    correlation_id = Column(Text, nullable=True, index=True)
    last_error_category = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=True)
    phone = Column(Text, unique=True, nullable=True)
    # Canonical E.164 identity key. `phone` remains the legacy national-format
    # projection until older clients and integrations have migrated.
    phone_canonical = Column(Text, unique=True, nullable=True)
    identity_review_required = Column(Boolean, nullable=False, default=False, server_default="false")
    phone_verified_at = Column(DateTime(timezone=True), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    full_name = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=True)
    auth_token_version = Column(Integer, nullable=False, default=0, server_default="0")
    role = Column(Text, nullable=False)
    location = Column(Text, nullable=True)
    district = Column(Text, nullable=True)
    state = Column(Text, nullable=True)
    state_id = Column(UUID(as_uuid=True), ForeignKey("geo_states.id"), nullable=True)
    district_id = Column(UUID(as_uuid=True), ForeignKey("geo_districts.id"), nullable=True)
    subdistrict_id = Column(UUID(as_uuid=True), ForeignKey("geo_subdistricts.id"), nullable=True)
    location_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    coordinate_source = Column(Text, nullable=True)
    coordinate_confidence = Column(Numeric(3, 2), nullable=True)
    coordinate_accuracy_m = Column(Numeric(10, 2), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    account_status = Column(Text, nullable=False, default="ACTIVE", server_default="ACTIVE")
    restricted_until = Column(DateTime(timezone=True), nullable=True)
    restriction_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (CheckConstraint("role IN ('farmer','buyer','fpo','admin','operator','support','reviewer','fraud_reviewer')", name="ck_users_role"),)


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    land_area_acres = Column(Numeric(10, 2), nullable=True)
    primary_crops = Column(ARRAY(Text), nullable=True)
    bank_account_encrypted = Column(Text, nullable=True)
    ifsc_encrypted = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class BuyerProfile(Base):
    __tablename__ = "buyer_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    business_name = Column(Text, nullable=False)
    business_type = Column(Text, nullable=True)
    license_number = Column(Text, nullable=True)
    crops_interested = Column(ARRAY(Text), nullable=True)
    min_quantity_quintals = Column(Numeric(10, 2), nullable=True)
    max_quantity_quintals = Column(Numeric(10, 2), nullable=True)
    preferred_grade = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    business_verification_status = Column(Text, nullable=False, default="UNVERIFIED", server_default="UNVERIFIED")
    rating = Column(Numeric(3, 2), default=0)
    total_transactions = Column(Integer, default=0)
    location_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint(
            "business_type IN ('trader','processor','exporter','retailer') OR business_type IS NULL",
            name="ck_buyer_type",
        ),
    )


class FPOProfile(Base):
    __tablename__ = "fpo_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    organization_name = Column(Text, nullable=False)
    registration_number = Column(Text, nullable=True)
    organization_verification_status = Column(Text, nullable=False, default="UNVERIFIED", server_default="UNVERIFIED")
    member_count = Column(Integer, default=0)
    total_land_acres = Column(Numeric(12, 2), nullable=True)
    primary_crops = Column(ARRAY(Text), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class FPOMember(Base):
    __tablename__ = "fpo_members"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fpo_id = Column(UUID(as_uuid=True), ForeignKey("fpo_profiles.id", ondelete="CASCADE"), nullable=False)
    farmer_name = Column(Text, nullable=False)
    phone = Column(Text, nullable=True)
    village = Column(Text, nullable=True)
    district = Column(Text, nullable=True)
    land_acres = Column(Numeric(10, 2), nullable=True, default=0.0)
    primary_crop = Column(Text, nullable=False)
    ready_quantity_qtl = Column(Numeric(10, 2), nullable=True, default=0.0)
    grade = Column(Text, nullable=True, default="A")
    member_code = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("fpo_id", "member_code", name="uq_fpo_member_code"),)


class StaffActionGrant(Base):
    """Short-lived, action-scoped reauthentication grant for staff actions."""

    __tablename__ = "staff_action_grants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Text, nullable=True, index=True)
    action_family = Column(Text, nullable=False)
    token_hash = Column(Text, nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FraudCase(Base):
    """Evidence-backed review signal; never a finding of wrongdoing."""

    __tablename__ = "fraud_cases"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_type = Column(Text, nullable=False)
    subject_id = Column(Text, nullable=False, index=True)
    signal_type = Column(Text, nullable=False)
    rule_id = Column(Text, nullable=False)
    rule_version = Column(Text, nullable=False)
    severity = Column(Text, nullable=False, default="LOW")
    evidence_refs = Column(JSON, nullable=False, default=list)
    status = Column(Text, nullable=False, default="OPEN")
    assigned_reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    decision = Column(Text, nullable=True)
    decision_reason = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("subject_type", "subject_id", "signal_type", "rule_version", name="uq_fraud_case_signal"),
        CheckConstraint("severity IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_fraud_case_severity"),
        CheckConstraint("status IN ('OPEN','IN_REVIEW','ACTION_REQUIRED','RESOLVED','DISMISSED')", name="ck_fraud_case_status"),
    )


class SupportCase(Base):
    __tablename__ = "support_cases"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_reference = Column(Text, unique=True, nullable=False)
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(Text, nullable=False)
    subject = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    linked_grievance_id = Column(UUID(as_uuid=True), ForeignKey("disputes.id"), nullable=True)
    status = Column(Text, nullable=False, default="OPEN")
    assigned_staff_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SupportNote(Base):
    __tablename__ = "support_notes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("support_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IncidentRecord(Base):
    __tablename__ = "incident_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    severity = Column(Text, nullable=False, default="MEDIUM")
    status = Column(Text, nullable=False, default="OPEN")
    affected_capability = Column(Text, nullable=True)
    summary = Column(Text, nullable=False)
    runbook_ref = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)


class FPOIntake(Base):
    __tablename__ = "fpo_intakes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_id = Column(Text, unique=True, nullable=False)
    fpo_id = Column(UUID(as_uuid=True), ForeignKey("fpo_profiles.id"), nullable=False, index=True)
    member_id = Column(UUID(as_uuid=True), ForeignKey("fpo_members.id"), nullable=False, index=True)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    crop_name = Column(Text, nullable=False)
    grade = Column(Text, nullable=True)
    gross_quantity = Column(Numeric(12, 3), nullable=False)
    tare_quantity = Column(Numeric(12, 3), nullable=False, default=0)
    net_quantity = Column(Numeric(12, 3), nullable=False)
    unit = Column(Text, nullable=False)
    canonical_quantity = Column(Numeric(12, 3), nullable=False)
    settlement_rate = Column(Numeric(12, 2), nullable=True)
    notes = Column(Text, nullable=True)
    correction_of_intake_id = Column(UUID(as_uuid=True), ForeignKey("fpo_intakes.id"), nullable=True)
    correction_reason = Column(Text, nullable=True)
    correction_actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_voided = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FPOPool(Base):
    __tablename__ = "fpo_pools"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_id = Column(Text, unique=True, nullable=False)
    fpo_id = Column(UUID(as_uuid=True), ForeignKey("fpo_profiles.id"), nullable=False, index=True)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    crop_name = Column(Text, nullable=False)
    grade = Column(Text, nullable=True)
    quantity = Column(Numeric(12, 3), nullable=False)
    status = Column(Text, nullable=False, default="READY")
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FPOPoolContribution(Base):
    __tablename__ = "fpo_pool_contributions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pool_id = Column(UUID(as_uuid=True), ForeignKey("fpo_pools.id"), nullable=False, index=True)
    intake_id = Column(UUID(as_uuid=True), ForeignKey("fpo_intakes.id"), nullable=False, index=True)
    member_id = Column(UUID(as_uuid=True), ForeignKey("fpo_members.id"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    __table_args__ = (UniqueConstraint("pool_id", "intake_id", name="uq_fpo_pool_intake_contribution"),)


class FPOMemberTradeAllocation(Base):
    __tablename__ = "fpo_member_trade_allocations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False, index=True)
    pool_id = Column(UUID(as_uuid=True), ForeignKey("fpo_pools.id"), nullable=False)
    contribution_id = Column(UUID(as_uuid=True), ForeignKey("fpo_pool_contributions.id"), nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey("fpo_members.id"), nullable=False)
    sold_quantity = Column(Numeric(12, 3), nullable=False)
    gross_allocation = Column(Numeric(12, 2), nullable=False)
    status = Column(Text, nullable=False, default="PROJECTED")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("transaction_id", "contribution_id", name="uq_fpo_trade_contribution"),)


class AuthSession(Base):
    """Server-side refresh-token family state; raw bearer tokens are never stored."""

    __tablename__ = "auth_sessions"
    id = Column(Text, primary_key=True)  # stable session id carried in access/refresh JWTs
    family_id = Column(Text, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_hash = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_reason = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)


class OtpChallenge(Base):
    __tablename__ = "otp_challenges"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Keyed digest prevents retained OTP challenges from exposing phone numbers.
    phone_hash = Column(Text, nullable=False, index=True)
    code_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")
    max_attempts = Column(Integer, nullable=False, default=3, server_default="3")
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    request_ip_hash = Column(Text, nullable=True)
    delivery_provider = Column(Text, nullable=True)
    __table_args__ = (Index("ix_otp_phone_created", "phone_hash", "created_at"),)


class PhoneIdentityConflict(Base):
    __tablename__ = "phone_identity_conflicts"
    canonical_phone = Column(Text, primary_key=True)
    legacy_user_ids = Column(JSON, nullable=False)
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolution_status = Column(Text, nullable=False, default="needs_review", server_default="needs_review")


class ConsentRecord(Base):
    __tablename__ = "consent_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_type = Column(Text, nullable=False)
    policy_version = Column(Text, nullable=False)
    accepted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)
    source = Column(Text, nullable=False, default="web_registration", server_default="web_registration")
    user_agent = Column(Text, nullable=True)
    __table_args__ = (
        CheckConstraint(
            "policy_type IN ('terms','privacy_notice','marketing','location_gps')",
            name="ck_consent_policy_type",
        ),
        Index("ix_consent_user_policy_accepted", "user_id", "policy_type", "accepted_at"),
    )


class VerificationRecord(Base):
    __tablename__ = "verification_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    dimension = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="UNVERIFIED", server_default="UNVERIFIED")
    method = Column(Text, nullable=True)
    provider = Column(Text, nullable=True)
    provider_reference = Column(Text, nullable=True)
    reason_code = Column(Text, nullable=True)
    evidence_metadata = Column(JSON, nullable=False, default=dict, server_default="{}")
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        CheckConstraint("dimension IN ('phone','email','identity','business','gst','bank','organization')", name="ck_verification_dimension"),
        CheckConstraint("status IN ('UNVERIFIED','PENDING_REVIEW','VERIFIED','REJECTED','NEEDS_MORE_INFORMATION','UNAVAILABLE')", name="ck_verification_status"),
        Index("ix_verification_user_dimension_created", "user_id", "dimension", "created_at"),
    )


class PasswordResetGrant(Base):
    __tablename__ = "password_reset_grants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(Text, nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PrivacyRequest(Base):
    __tablename__ = "privacy_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    request_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="RECEIVED", server_default="RECEIVED")
    user_note = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        CheckConstraint("request_type IN ('access','correction','erasure')", name="ck_privacy_request_type"),
        CheckConstraint("status IN ('RECEIVED','IN_REVIEW','COMPLETED','DECLINED')", name="ck_privacy_request_status"),
    )


class Crop(Base):
    __tablename__ = "crops"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, unique=True, nullable=False)
    slug = Column(Text, unique=True, nullable=True)
    name_marathi = Column(Text, nullable=True)
    name_hindi = Column(Text, nullable=True)
    aliases = Column(JSON, nullable=False, default=list)
    category = Column(Text, nullable=True)
    unit = Column(Text, default="quintal")
    valid_units = Column(JSON, nullable=False, default=lambda: ["quintal"])
    agmarknet_name = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_tradable = Column(Boolean, nullable=False, default=True)
    image_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    varieties = relationship("CropVariety", cascade="all, delete-orphan", order_by="CropVariety.name")
    quality_specs = relationship("CropQualitySpec", cascade="all, delete-orphan", order_by="CropQualitySpec.grade")


@event.listens_for(Crop, "before_insert")
def _set_crop_slug(_mapper, _connection, target: Crop) -> None:
    if target.slug:
        return
    import re
    import unicodedata

    normalized = unicodedata.normalize("NFKD", target.name).encode("ascii", "ignore").decode().lower()
    target.slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or f"crop-{str(target.id or uuid.uuid4())[:8]}"


class CropVariety(Base):
    __tablename__ = "crop_varieties"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    name = Column(Text, nullable=False)
    name_hindi = Column(Text, nullable=True)
    name_marathi = Column(Text, nullable=True)
    code = Column(Text, nullable=True)
    agmarknet_name = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_tradable = Column(Boolean, nullable=False, default=True)
    __table_args__ = (UniqueConstraint("crop_id", "name", name="uq_crop_variety"),)


class CropQualitySpec(Base):
    __tablename__ = "crop_quality_specs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    variety_id = Column(UUID(as_uuid=True), ForeignKey("crop_varieties.id"), nullable=True)
    grade = Column(Text, nullable=False)
    moisture_max_pct = Column(Numeric(5, 2), nullable=True)
    foreign_matter_max_pct = Column(Numeric(5, 2), nullable=True)
    size_min_mm = Column(Numeric(7, 2), nullable=True)
    size_max_mm = Column(Numeric(7, 2), nullable=True)
    damage_max_pct = Column(Numeric(5, 2), nullable=True)
    description = Column(Text, nullable=True)
    source_ref = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (
        UniqueConstraint("crop_id", "variety_id", "grade", name="uq_crop_quality_grade"),
        CheckConstraint("moisture_max_pct IS NULL OR (moisture_max_pct >= 0 AND moisture_max_pct <= 100)", name="ck_quality_moisture_pct"),
        CheckConstraint("damage_max_pct IS NULL OR (damage_max_pct >= 0 AND damage_max_pct <= 100)", name="ck_quality_damage_pct"),
    )


class Market(Base):
    __tablename__ = "markets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    name_marathi = Column(Text, nullable=True)
    district = Column(Text, nullable=True)
    state = Column(Text, nullable=True)
    state_id = Column(UUID(as_uuid=True), ForeignKey("geo_states.id"), nullable=True)
    district_id = Column(UUID(as_uuid=True), ForeignKey("geo_districts.id"), nullable=True)
    subdistrict_id = Column(UUID(as_uuid=True), ForeignKey("geo_subdistricts.id"), nullable=True)
    normalized_name = Column(Text, nullable=True)
    outlet_type = Column(Text, nullable=True)
    source_registry_id = Column(UUID(as_uuid=True), ForeignKey("data_source_registry.id"), nullable=True)
    source_ref = Column(Text, nullable=True)
    source_confidence = Column(Numeric(3, 2), nullable=True)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    location_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    coordinate_source = Column(Text, nullable=True)
    coordinate_confidence = Column(Numeric(3, 2), nullable=True)
    verification_status = Column(Text, nullable=False, default="needs_review")
    verification_method = Column(Text, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    external_identifier = Column(Text, nullable=True)
    operating_days = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    market_type = Column(Text, default="APMC")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        Index("ix_markets_geog", "location_geog", postgresql_using="gist"),
        Index("ix_markets_source_ref", "source_registry_id", "source_ref", unique=True),
        Index("ix_markets_normalized_region", "normalized_name", "state_id", "district_id"),
        CheckConstraint(
            "verification_status IN ('unverified','needs_review','verified','rejected','inactive')",
            name="ck_market_verification_status",
        ),
        CheckConstraint(
            "coordinate_confidence IS NULL OR (coordinate_confidence >= 0 AND coordinate_confidence <= 1)",
            name="ck_market_coordinate_confidence",
        ),
        CheckConstraint(
            "source_confidence IS NULL OR (source_confidence >= 0 AND source_confidence <= 1)",
            name="ck_market_source_confidence",
        ),
    )


class PriceSource(Base):
    __tablename__ = "price_sources"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, unique=True, nullable=False)
    url = Column(Text, nullable=True)
    adapter = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    registry_id = Column(UUID(as_uuid=True), ForeignKey("data_source_registry.id"), nullable=True)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("price_sources.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Text, nullable=False, default="running")
    records_fetched = Column(Integer, default=0)
    records_ok = Column(Integer, default=0)
    records_accepted = Column(Integer, default=0, nullable=False)
    records_updated = Column(Integer, default=0, nullable=False)
    records_unchanged = Column(Integer, default=0, nullable=False)
    records_rejected = Column(Integer, default=0)
    records_quarantined = Column(Integer, default=0, nullable=False)
    unresolved_markets = Column(Integer, default=0, nullable=False)
    unresolved_crops = Column(Integer, default=0, nullable=False)
    duration_ms = Column(Integer, nullable=True)
    provider_failure = Column(Text, nullable=True)
    scope_json = Column(JSON, nullable=True)
    parser_version = Column(Text, nullable=True)
    error = Column(Text, nullable=True)


class PriceObservation(Base):
    __tablename__ = "price_observations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    variety_id = Column(UUID(as_uuid=True), ForeignKey("crop_varieties.id"), nullable=True)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)
    price_date = Column(Date, nullable=False)
    fetched_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
    min_price = Column(Numeric(10, 2), nullable=False)
    modal_price = Column(Numeric(10, 2), nullable=False)
    max_price = Column(Numeric(10, 2), nullable=False)
    grade = Column(Text, nullable=True)
    price_unit = Column(Text, nullable=True)
    source_unit = Column(Text, nullable=True)
    unit_provenance = Column(Text, nullable=True)
    arrival_quantity = Column(Numeric(12, 3), nullable=True)
    arrival_unit = Column(Text, nullable=True)
    volume_tonnes = Column(Numeric(10, 2), nullable=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("price_sources.id"), nullable=True)
    source_record_id = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now())
    ingestion_run_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_runs.id"), nullable=True)
    parser_version = Column(Text, nullable=True)
    normalization_version = Column(Text, nullable=True)
    raw_payload_hash = Column(Text, nullable=True)
    observation_key = Column(Text, nullable=False)
    quality_status = Column(Text, nullable=False, default="MEDIUM")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("observation_key", name="uq_price_observation_key"),
        CheckConstraint("modal_price > 0", name="ck_modal_positive"),
        CheckConstraint("quality_status IN ('HIGH','MEDIUM','LOW')", name="ck_quality"),
        Index("ix_price_obs_crop_market_date", "crop_id", "market_id", "price_date"),
        Index("ix_price_obs_crop_date_market", "crop_id", "price_date", "market_id"),
        Index("ix_price_obs_source_fetched", "source_id", "fetched_at"),
    )


class Lot(Base):
    __tablename__ = "lots"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_id = Column(Text, unique=True, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=True)
    crop_name = Column(Text, nullable=False)
    variety_id = Column(UUID(as_uuid=True), ForeignKey("crop_varieties.id"), nullable=True)
    grade = Column(Text, nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit = Column(Text, default="quintal")
    original_quantity = Column(Numeric(12, 3), nullable=True)
    original_unit = Column(Text, nullable=True)
    asking_price = Column(Numeric(12, 2), nullable=True)
    market_reference_price = Column(Numeric(12, 2), nullable=True)
    location_text = Column(Text, nullable=False)
    district = Column(Text, nullable=True)
    location_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    harvest_date = Column(Date, nullable=True)
    available_from = Column(Date, nullable=True)
    available_until = Column(Date, nullable=True)
    status = Column(Text, nullable=False, default="DRAFT")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_lot_qty_pos"),
      CheckConstraint("grade IN ('A','B','C','UNSPECIFIED')", name="ck_lot_grade"),
        CheckConstraint(
            "status IN ('DRAFT','PUBLISHED','RESERVED','PARTIALLY_ALLOCATED','SOLD','FULFILLED','CANCELLED','EXPIRED','active','matched','sold','expired','cancelled')",
            name="ck_lot_status",
        ),
        Index("ix_lots_owner", "owner_id"),
        Index("ix_lots_status", "status"),
        Index("ix_lots_public_id", "public_id"),
        Index("ix_lots_geog", "location_geog", postgresql_using="gist"),
    )


class LotAllocation(Base):
    __tablename__ = "lot_allocations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("offers.id"), nullable=True)
    allocated_quantity = Column(Numeric(12, 2), nullable=False)
    fulfilled_quantity = Column(Numeric(12, 2), default=0)
    status = Column(Text, default="ALLOCATED")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("allocated_quantity > 0", name="ck_alloc_qty"),
        Index("ix_alloc_lot", "lot_id"),
    )


class BuyerRequirement(Base):
    __tablename__ = "buyer_requirements"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=True)
    crop_name = Column(Text, nullable=False)
    variety_id = Column(UUID(as_uuid=True), ForeignKey("crop_varieties.id"), nullable=True)
    grade = Column(Text, nullable=True)
    quantity_min = Column(Numeric(12, 2), nullable=True)
    quantity_max = Column(Numeric(12, 2), nullable=True)
    target_price = Column(Numeric(12, 2), nullable=True)
    location_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    max_distance_km = Column(Numeric(10, 2), nullable=True)
    required_from = Column(Date, nullable=True)
    required_until = Column(Date, nullable=True)
    delivery_window = Column(Text, nullable=True)
    storage_requirements = Column(JSONB, nullable=True)
    quality_requirements = Column(JSONB, nullable=True)
    requested_quantity = Column(Numeric(12, 3), nullable=True)
    requested_unit = Column(Text, nullable=True)
    canonical_quantity = Column(Numeric(12, 2), nullable=True)
    committed_quantity = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(Text, nullable=False, default="DRAFT")
    location_text = Column(Text, nullable=True)
    allow_partial = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MatchRuleSet(Base):
    __tablename__ = "match_rulesets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(Text, unique=True, nullable=False)
    weights = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Match(Base):
    __tablename__ = "matches"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    buyer_requirement_id = Column(UUID(as_uuid=True), ForeignKey("buyer_requirements.id"), nullable=True)
    ruleset_id = Column(UUID(as_uuid=True), ForeignKey("match_rulesets.id"), nullable=True)
    ruleset_version = Column(Text, nullable=True)
    component_scores = Column(JSONB, nullable=False)
    final_score = Column(Integer, nullable=False)
    explanation = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("lot_id", "buyer_id", "ruleset_version", name="uq_match_lot_buyer_ruleset"),
        Index("ix_matches_lot_score", "lot_id", "final_score"),
    )


class Offer(Base):
    __tablename__ = "offers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    price_per_unit = Column(Numeric(12, 2), nullable=False)
    total_value = Column(Numeric(12, 2), nullable=True)
    message = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Text, default="PENDING")
    parent_offer_id = Column(UUID(as_uuid=True), ForeignKey("offers.id"), nullable=True)
    buyer_requirement_id = Column(UUID(as_uuid=True), ForeignKey("buyer_requirements.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_offer_qty"),
        CheckConstraint(
            "status IN ('PENDING','COUNTERED','ACCEPTED','REJECTED','EXPIRED','CANCELLED','pending','accepted','rejected','expired','completed')",
            name="ck_offer_status",
        ),
        Index("ix_offers_lot", "lot_id"),
        Index("ix_offers_buyer", "buyer_id"),
    )


class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("offers.id"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    status = Column(Text, default="ACTIVE")
    reserved_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (CheckConstraint("status IN ('ACTIVE','EXPIRED','CONSUMED','CANCELLED')", name="ck_res_status"),)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_id = Column(Text, unique=True, nullable=True)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    allocation_id = Column(UUID(as_uuid=True), ForeignKey("lot_allocations.id"), nullable=True)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("offers.id"), nullable=True)
    status = Column(Text, default="CREATED")
    gross_value = Column(Numeric(12, 2), nullable=True)
    transport_cost = Column(Numeric(12, 2), nullable=True)
    storage_cost = Column(Numeric(12, 2), nullable=True)
    fees = Column(Numeric(12, 2), nullable=True)
    net_realization = Column(Numeric(12, 2), nullable=True)
    idempotency_key = Column(Text, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint(
            "status IN ('CREATED','PAYMENT_PENDING','PAYMENT_CONFIRMED','PROCESSING','READY_FOR_DISPATCH','IN_TRANSIT','DELIVERED','COMPLETED','DISPUTED','CANCELLED','REFUNDED','offer_accepted','payment_pending','payment_received','completed')",
            name="ck_txn_status",
        ),
        Index("ix_txn_seller", "seller_id"),
        Index("ix_txn_buyer", "buyer_id"),
        Index("ix_txn_public_id", "public_id"),
    )

    term_snapshot = relationship("TradeTermSnapshot", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    events = relationship("TradeEvent", back_populates="transaction", cascade="all, delete-orphan", order_by="TradeEvent.created_at")


class TradeTermSnapshot(Base):
    __tablename__ = "trade_term_snapshots"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), unique=True, nullable=False)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    crop_name = Column(Text, nullable=False)
    grade = Column(Text, nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit = Column(Text, default="quintal")
    price_per_unit = Column(Numeric(12, 2), nullable=False)
    gross_value = Column(Numeric(12, 2), nullable=False)
    estimated_net_realization = Column(Numeric(12, 2), nullable=True)
    delivery_window = Column(Text, nullable=True)
    pickup_location = Column(Text, nullable=True)
    delivery_location = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_trade_terms_txn", "transaction_id"),)

    transaction = relationship("Transaction", back_populates="term_snapshot")


class TradeEvent(Base):
    __tablename__ = "trade_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    actor_role = Column(Text, nullable=True)
    event_type = Column(Text, nullable=False)
    from_status = Column(Text, nullable=True)
    to_status = Column(Text, nullable=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    # Participant statements and provider/reviewer evidence remain distinguishable
    # in the canonical Trade Room timeline.
    source_kind = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=True)
    idempotency_key = Column(Text, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_trade_events_txn", "transaction_id"), Index("ix_trade_events_created", "created_at"))

    transaction = relationship("Transaction", back_populates="events")


class TransactionItem(Base):
    __tablename__ = "transaction_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)


class Payment(Base):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    provider = Column(Text, nullable=False)
    provider_reference = Column(Text, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(Text, default="INR")
    status = Column(Text, default="PENDING")
    source_kind = Column(Text, nullable=False, default="UNKNOWN_LEGACY", server_default="UNKNOWN_LEGACY")
    reported_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    idempotency_key = Column(Text, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    pickup_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    delivery_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    distance_km = Column(Numeric(10, 2), nullable=True)
    estimated_transport_cost = Column(Numeric(12, 2), nullable=True)
    status = Column(Text, default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StorageFacility(Base):
    __tablename__ = "storage_facilities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    type = Column(Text, nullable=True)
    capacity = Column(Numeric(12, 2), nullable=True)
    available_capacity = Column(Numeric(12, 2), nullable=True)
    location_text = Column(Text, nullable=True)
    location_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    cost_per_unit = Column(Numeric(12, 2), nullable=True)
    services = Column(JSONB, nullable=True)
    contact = Column(Text, nullable=True)
    verification_status = Column(Text, default="PENDING")
    source_kind = Column(Text, nullable=False, default="UNKNOWN_LEGACY", server_default="UNKNOWN_LEGACY")
    status = Column(Text, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("available_capacity >= 0 OR available_capacity IS NULL", name="ck_storage_avail"),
    )


class TradeStorageRequest(Base):
    """A participant request awaiting confirmation; it does not reserve capacity."""

    __tablename__ = "trade_storage_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("storage_facilities.id"), nullable=False)
    requested_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="REQUESTED")
    idempotency_key = Column(Text, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_trade_storage_request_qty"),
        CheckConstraint("status = 'REQUESTED'", name="ck_trade_storage_request_pending_only"),
        Index("ix_trade_storage_request_txn", "transaction_id"),
    )


class Dispute(Base):
    __tablename__ = "disputes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True)
    raised_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Text, default="OPEN")
    resolution = Column(Text, nullable=True)
    operator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint(
            "status IN ('OPEN','UNDER_REVIEW','RESOLVED','REJECTED','ESCALATED','open','under_review','resolved','closed')",
            name="ck_dispute_status",
        ),
    )


class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispute_id = Column(UUID(as_uuid=True), ForeignKey("disputes.id"), nullable=True)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=True)
    uploader_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    s3_key = Column(Text, nullable=False)
    file_hash = Column(Text, nullable=False)
    mime_type = Column(Text, nullable=True)
    classification = Column(Text, nullable=False, default="UNKNOWN_LEGACY", server_default="UNKNOWN_LEGACY")
    provenance_status = Column(Text, nullable=False, default="UNKNOWN_LEGACY", server_default="UNKNOWN_LEGACY")
    file_size_bytes = Column(Integer, nullable=True)
    original_filename = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    metadata_json = Column("metadata", JSON, nullable=True)
    is_read = Column(Boolean, default=False)
    related_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_notif_user_read", "user_id", "is_read"),)


class WebPushSubscription(Base):
    """One explicitly authorized browser endpoint owned by one platform user."""

    __tablename__ = "web_push_subscriptions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    endpoint = Column(Text, nullable=False)
    endpoint_hash = Column(Text, nullable=False, unique=True)
    p256dh = Column(Text, nullable=False)
    auth = Column(Text, nullable=False)
    language = Column(Text, nullable=False, default="en", server_default="en")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        Index("ix_web_push_subscription_user_active", "user_id", "is_active"),
    )


class WebPushDelivery(Base):
    """Deduplication receipt for one canonical notification/device pair."""

    __tablename__ = "web_push_deliveries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("web_push_subscriptions.id", ondelete="CASCADE"), nullable=False)
    status = Column(Text, nullable=False, default="PENDING", server_default="PENDING")
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    lease_until = Column(DateTime(timezone=True), nullable=True)
    last_outcome = Column(Text, nullable=True)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("notification_id", "subscription_id", name="uq_web_push_notification_subscription"),
        Index("ix_web_push_delivery_status_next", "status", "next_attempt_at"),
    )


class WebPushAttempt(Base):
    """Privacy-minimal immutable attempt outcome; never stores endpoint or payload."""

    __tablename__ = "web_push_attempts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_id = Column(UUID(as_uuid=True), ForeignKey("web_push_deliveries.id", ondelete="CASCADE"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    outcome = Column(Text, nullable=False)
    status_code = Column(Integer, nullable=True)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        UniqueConstraint("delivery_id", "attempt_number", name="uq_web_push_delivery_attempt_number"),
        Index("ix_web_push_attempted_at", "attempted_at"),
    )


class PriceAlertRule(Base):
    """A user-authored threshold over future official reported observations."""

    __tablename__ = "price_alert_rules"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)
    variety_id = Column(UUID(as_uuid=True), ForeignKey("crop_varieties.id"), nullable=True)
    grade = Column(Text, nullable=True)
    threshold = Column(Numeric(12, 2), nullable=False)
    direction = Column(Text, nullable=False)
    price_unit = Column(Text, nullable=False, default="INR/quintal", server_default="INR/quintal")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    is_armed = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        CheckConstraint("threshold > 0", name="ck_price_alert_threshold_positive"),
        CheckConstraint("direction IN ('AT_OR_ABOVE','AT_OR_BELOW')", name="ck_price_alert_direction"),
        CheckConstraint("price_unit = 'INR/quintal'", name="ck_price_alert_unit"),
        Index("ix_price_alert_user_active", "user_id", "is_active"),
    )


class PriceAlertEvaluation(Base):
    """Persisted evaluation receipt; unique per alert and source observation."""

    __tablename__ = "price_alert_evaluations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("price_alert_rules.id", ondelete="CASCADE"), nullable=False)
    observation_id = Column(UUID(as_uuid=True), ForeignKey("price_observations.id"), nullable=False)
    triggered = Column(Boolean, nullable=False)
    evaluated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("alert_id", "observation_id", name="uq_price_alert_observation"),
        Index("ix_price_alert_eval_alert", "alert_id", "evaluated_at"),
    )


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    key = Column(Text, primary_key=True)
    response_status = Column(Integer, nullable=True)
    response_body = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
