import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class TradeTermSnapshotResponse(BaseModel):
    model_config = {"from_attributes": True}
    crop_name: str
    grade: str
    quantity: float
    unit: str = "quintal"
    price_per_unit: float
    gross_value: float
    estimated_net_realization: float | None = None
    delivery_window: str | None = None
    pickup_location: str | None = None
    delivery_location: str | None = None
    created_at: datetime


class TradeEventResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    transaction_id: uuid.UUID
    actor_id: uuid.UUID | None = None
    actor_role: str | None = None
    event_type: str
    from_status: str | None = None
    to_status: str | None = None
    title: str
    description: str | None = None
    source_kind: str | None = None
    metadata: dict | None = None
    created_at: datetime


class NextActionResponse(BaseModel):
    action_required: bool
    responsible_role: str
    action_title: str
    action_description: str
    action_type: str
    is_current_user_action: bool


class PartySummary(BaseModel):
    id: uuid.UUID | None = None
    full_name: str | None = None
    business_name: str | None = None
    role: str
    location: str | None = None
    district: str | None = None


class PaymentSummary(BaseModel):
    status: str
    gross_value: Decimal | None = None
    provider_connected: bool = False
    provider_verified: bool = False
    reports: list["PaymentReportSummary"] = Field(default_factory=list)
    legacy_unverified_count: int = 0
    note: str | None = None


class PaymentReportSummary(BaseModel):
    id: uuid.UUID
    amount: Decimal
    currency: str
    reference: str | None = None
    status: str
    source_kind: str
    reported_at: datetime
    reported_by_role: str | None = None
    seller_acknowledged: bool = False


class LogisticsSummary(BaseModel):
    status: str
    origin: str | None = None
    destination: str | None = None
    provider_connected: bool = False
    note: str | None = None


class QualitySummary(BaseModel):
    agreed_grade: str
    verification_status: str
    note: str | None = None


class TradeRoomResponse(BaseModel):
    id: uuid.UUID
    public_id: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    buyer: PartySummary
    seller: PartySummary
    terms: TradeTermSnapshotResponse | None = None
    payment: PaymentSummary
    logistics: LogisticsSummary
    quality: QualitySummary
    next_action: NextActionResponse
    timeline: list[TradeEventResponse]
    storage_requests: list[dict] = Field(default_factory=list)
    evidence: list[dict] = Field(default_factory=list)
    viewer_party: Literal["buyer", "seller", "operator"]


class TradeTransitionRequest(BaseModel):
    to_status: str = Field(min_length=3, max_length=50)
    reason: str | None = Field(default=None, max_length=500)


class AddTradeNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=1000)


class PaymentReportRequest(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    reference: str = Field(min_length=1, max_length=120)
    currency: Literal["INR"] = "INR"


class QualityReportRequest(BaseModel):
    kind: Literal["PARTICIPANT_CLAIM", "OBSERVATION"]
    details: str = Field(min_length=3, max_length=1000)
    attributes: dict[str, str] = Field(default_factory=dict, max_length=20)


class WeighmentRequest(BaseModel):
    gross_quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    tare_quantity: Decimal = Field(ge=0, max_digits=12, decimal_places=3)
    unit: str = Field(min_length=1, max_length=24)


class LogisticsUpdateRequest(BaseModel):
    kind: Literal["PICKUP_REPORTED", "DISPATCH_REPORTED", "DELIVERY_REPORTED", "RECEIPT_CONFIRMED"]
    details: str | None = Field(default=None, max_length=500)
    evidence_id: uuid.UUID | None = None


class StorageRequestBody(BaseModel):
    facility_id: uuid.UUID
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unit: str = Field(min_length=1, max_length=24)
