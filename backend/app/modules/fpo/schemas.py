from pydantic import BaseModel, Field


class FPOMemberCreateRequest(BaseModel):
    farmer_name: str = Field(..., min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    village: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    land_acres: float = Field(default=0.0, ge=0.0)
    primary_crop: str = Field(..., min_length=2, max_length=50)
    ready_quantity_qtl: float = Field(default=0.0, ge=0.0)
    grade: str = Field(default="A", max_length=10)


class FPOMemberResponse(BaseModel):
    id: str
    farmer_name: str
    phone: str | None = None
    village: str | None = None
    district: str | None = None
    land_acres: float
    primary_crop: str
    ready_quantity_qtl: float
    grade: str
    created_at: str | None = None


class FPOAggregateLotRequest(BaseModel):
    crop: str = Field(..., min_length=2, max_length=50)
    quantity: float = Field(..., gt=0)
    unit: str = Field(default="quintal", max_length=20)
    grade: str = Field(default="A", max_length=10)
    asking_price: float = Field(..., gt=0)
    location_text: str = Field(..., min_length=2)
    district: str | None = None
    member_ids: list[str] = Field(default_factory=list)
    notes: str | None = None


class FPOSummaryResponse(BaseModel):
    organization_name: str
    total_members: int
    active_lots: int
    total_volume_qtl: float
    pending_offers: int
    pending_offers_value: float
    completed_deals: int
    total_revenue: float
