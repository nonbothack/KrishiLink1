import uuid
from datetime import datetime

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
    created_at: datetime


class NextActionResponse(BaseModel):
    action_required: bool
    responsible_role: str
    action_title: str
    action_description: str
    action_type: str
    is_current_user_action: bool


class PartySummary(BaseModel):
    id: uuid.UUID
    full_name: str
    role: str
    location: str | None = None
    district: str | None = None


class PaymentSummary(BaseModel):
    status: str
    gross_value: float
    transport_cost: float | None = None
    platform_fee: float | None = None
    net_realization: float | None = None
    is_sandbox: bool = True
    note: str


class LogisticsSummary(BaseModel):
    status: str
    origin: str | None = None
    destination: str | None = None
    carrier_status: str
    note: str


class QualitySummary(BaseModel):
    agreed_grade: str
    verification_status: str
    note: str


class TradeRoomResponse(BaseModel):
    id: uuid.UUID
    public_id: str
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


class TradeTransitionRequest(BaseModel):
    to_status: str = Field(min_length=3, max_length=50)
    reason: str | None = Field(default=None, max_length=500)


class AddTradeNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=1000)
