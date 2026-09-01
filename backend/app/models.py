import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    ARRAY,
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
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())

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
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=True)
    phone = Column(Text, unique=True, nullable=True)
    full_name = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=True)
    role = Column(Text, nullable=False)
    location = Column(Text, nullable=True)
    district = Column(Text, nullable=True)
    state = Column(Text, nullable=False, default="Maharashtra")
    location_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        CheckConstraint("role IN ('farmer','buyer','fpo','admin','operator')", name="ck_users_role"),
    )

class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    land_area_acres = Column(Numeric(10,2), nullable=True)
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
    min_quantity_quintals = Column(Numeric(10,2), nullable=True)
    max_quantity_quintals = Column(Numeric(10,2), nullable=True)
    preferred_grade = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    rating = Column(Numeric(3,2), default=0)
    total_transactions = Column(Integer, default=0)
    location_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("business_type IN ('trader','processor','exporter','retailer') OR business_type IS NULL", name="ck_buyer_type"),
    )

class FPOProfile(Base):
    __tablename__ = "fpo_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    organization_name = Column(Text, nullable=False)
    registration_number = Column(Text, nullable=True)
    member_count = Column(Integer, default=0)
    total_land_acres = Column(Numeric(12,2), nullable=True)
    primary_crops = Column(ARRAY(Text), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class Crop(Base):
    __tablename__ = "crops"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, unique=True, nullable=False)
    name_marathi = Column(Text, nullable=True)
    name_hindi = Column(Text, nullable=True)
    category = Column(Text, nullable=True)
    unit = Column(Text, default="quintal")
    image_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CropVariety(Base):
    __tablename__ = "crop_varieties"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    name = Column(Text, nullable=False)
    code = Column(Text, nullable=True)
    __table_args__ = (UniqueConstraint("crop_id","name", name="uq_crop_variety"),)

class Market(Base):
    __tablename__ = "markets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    name_marathi = Column(Text, nullable=True)
    district = Column(Text, nullable=False)
    state = Column(Text, default="Maharashtra")
    latitude = Column(Numeric(10,7), nullable=True)
    longitude = Column(Numeric(10,7), nullable=True)
    location_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    market_type = Column(Text, default="APMC")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_markets_geog", "location_geog", postgresql_using="gist"),)

class PriceSource(Base):
    __tablename__ = "price_sources"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, unique=True, nullable=False)
    url = Column(Text, nullable=True)
    adapter = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)

class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("price_sources.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Text, nullable=False, default="running")
    records_fetched = Column(Integer, default=0)
    records_ok = Column(Integer, default=0)
    records_rejected = Column(Integer, default=0)
    parser_version = Column(Text, nullable=True)
    error = Column(Text, nullable=True)

class PriceObservation(Base):
    __tablename__ = "price_observations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    variety_id = Column(UUID(as_uuid=True), ForeignKey("crop_varieties.id"), nullable=True)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)
    price_date = Column(Date, nullable=False)
    min_price = Column(Numeric(10,2), nullable=False)
    modal_price = Column(Numeric(10,2), nullable=False)
    max_price = Column(Numeric(10,2), nullable=False)
    volume_tonnes = Column(Numeric(10,2), nullable=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("price_sources.id"), nullable=True)
    source_record_id = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now())
    ingestion_run_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_runs.id"), nullable=True)
    parser_version = Column(Text, nullable=True)
    normalization_version = Column(Text, nullable=True)
    raw_payload_hash = Column(Text, nullable=True)
    quality_status = Column(Text, nullable=False, default="MEDIUM")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("crop_id","market_id","price_date","source_id", name="uq_price_obs"),
        CheckConstraint("modal_price > 0", name="ck_modal_positive"),
        CheckConstraint("quality_status IN ('HIGH','MEDIUM','LOW')", name="ck_quality"),
        Index("ix_price_obs_crop_market_date", "crop_id","market_id","price_date"),
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
    quantity = Column(Numeric(12,2), nullable=False)
    unit = Column(Text, default="quintal")
    asking_price = Column(Numeric(12,2), nullable=True)
    market_reference_price = Column(Numeric(12,2), nullable=True)
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
        CheckConstraint("grade IN ('A','B','C')", name="ck_lot_grade"),
        CheckConstraint("status IN ('DRAFT','PUBLISHED','RESERVED','PARTIALLY_ALLOCATED','SOLD','FULFILLED','CANCELLED','EXPIRED','active','matched','sold','expired','cancelled')", name="ck_lot_status"),
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
    allocated_quantity = Column(Numeric(12,2), nullable=False)
    fulfilled_quantity = Column(Numeric(12,2), default=0)
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
    quantity_min = Column(Numeric(12,2), nullable=True)
    quantity_max = Column(Numeric(12,2), nullable=True)
    target_price = Column(Numeric(12,2), nullable=True)
    location_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    max_distance_km = Column(Numeric(10,2), nullable=True)
    required_from = Column(Date, nullable=True)
    required_until = Column(Date, nullable=True)
    delivery_window = Column(Text, nullable=True)
    storage_requirements = Column(JSONB, nullable=True)
    quality_requirements = Column(JSONB, nullable=True)
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
        UniqueConstraint("lot_id","buyer_id","ruleset_version", name="uq_match_lot_buyer_ruleset"),
        Index("ix_matches_lot_score", "lot_id","final_score"),
    )

class Offer(Base):
    __tablename__ = "offers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    quantity = Column(Numeric(12,2), nullable=False)
    price_per_unit = Column(Numeric(12,2), nullable=False)
    total_value = Column(Numeric(12,2), nullable=True)
    message = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Text, default="PENDING")
    parent_offer_id = Column(UUID(as_uuid=True), ForeignKey("offers.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_offer_qty"),
        CheckConstraint("status IN ('PENDING','COUNTERED','ACCEPTED','REJECTED','EXPIRED','CANCELLED','pending','accepted','rejected','expired','completed')", name="ck_offer_status"),
        Index("ix_offers_lot", "lot_id"),
        Index("ix_offers_buyer", "buyer_id"),
    )

class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("offers.id"), nullable=False)
    quantity = Column(Numeric(12,2), nullable=False)
    status = Column(Text, default="ACTIVE")
    reserved_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','EXPIRED','CONSUMED','CANCELLED')", name="ck_res_status"),
    )

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
    gross_value = Column(Numeric(12,2), nullable=True)
    transport_cost = Column(Numeric(12,2), nullable=True)
    storage_cost = Column(Numeric(12,2), nullable=True)
    fees = Column(Numeric(12,2), nullable=True)
    net_realization = Column(Numeric(12,2), nullable=True)
    idempotency_key = Column(Text, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("status IN ('CREATED','PAYMENT_PENDING','PAYMENT_CONFIRMED','PROCESSING','READY_FOR_DISPATCH','IN_TRANSIT','DELIVERED','COMPLETED','DISPUTED','CANCELLED','REFUNDED','offer_accepted','payment_pending','payment_received','completed')", name="ck_txn_status"),
        Index("ix_txn_seller", "seller_id"),
        Index("ix_txn_buyer", "buyer_id"),
        Index("ix_txn_public_id", "public_id"),
    )

class TradeTermSnapshot(Base):
    __tablename__ = "trade_term_snapshots"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), unique=True, nullable=False)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    crop_name = Column(Text, nullable=False)
    grade = Column(Text, nullable=False)
    quantity = Column(Numeric(12,2), nullable=False)
    unit = Column(Text, default="quintal")
    price_per_unit = Column(Numeric(12,2), nullable=False)
    gross_value = Column(Numeric(12,2), nullable=False)
    estimated_net_realization = Column(Numeric(12,2), nullable=True)
    delivery_window = Column(Text, nullable=True)
    pickup_location = Column(Text, nullable=True)
    delivery_location = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        Index("ix_trade_terms_txn", "transaction_id"),
    )

class TradeEvent(Base):
    __tablename__ = "trade_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    actor_role = Column(Text, nullable=True)
    event_type = Column(Text, nullable=False)  # 'DOMAIN_EVENT', 'USER_NOTE'
    from_status = Column(Text, nullable=True)
    to_status = Column(Text, nullable=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        Index("ix_trade_events_txn", "transaction_id"),
        Index("ix_trade_events_created", "created_at"),
    )

class TransactionItem(Base):
    __tablename__ = "transaction_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=False)
    quantity = Column(Numeric(12,2), nullable=False)
    price = Column(Numeric(12,2), nullable=False)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    provider = Column(Text, nullable=False)
    provider_reference = Column(Text, nullable=True)
    amount = Column(Numeric(12,2), nullable=False)
    currency = Column(Text, default="INR")
    status = Column(Text, default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    pickup_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    delivery_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    distance_km = Column(Numeric(10,2), nullable=True)
    estimated_transport_cost = Column(Numeric(12,2), nullable=True)
    status = Column(Text, default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class StorageFacility(Base):
    __tablename__ = "storage_facilities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    type = Column(Text, nullable=True)
    capacity = Column(Numeric(12,2), nullable=True)
    available_capacity = Column(Numeric(12,2), nullable=True)
    location_text = Column(Text, nullable=True)
    location_geog = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    cost_per_unit = Column(Numeric(12,2), nullable=True)
    services = Column(JSONB, nullable=True)
    contact = Column(Text, nullable=True)
    verification_status = Column(Text, default="PENDING")
    status = Column(Text, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("available_capacity >= 0 OR available_capacity IS NULL", name="ck_storage_avail"),
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
    __table_args__ = (CheckConstraint("status IN ('OPEN','UNDER_REVIEW','RESOLVED','REJECTED','ESCALATED','open','under_review','resolved','closed')", name="ck_dispute_status"),)

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
    metadata_json = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    related_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_notif_user_read", "user_id","is_read"),)

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    key = Column(Text, primary_key=True)
    response_status = Column(Integer, nullable=True)
    response_body = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
