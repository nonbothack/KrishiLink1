from decimal import Decimal

from pydantic import BaseModel, Field


class FPOMemberCreateRequest(BaseModel):
    farmer_name: str = Field(..., min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    village: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    land_acres: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)
    primary_crop: str = Field(..., min_length=2, max_length=50)
    # Compatibility-only: intake records are the quantity authority.
    ready_quantity_qtl: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)
    grade: str = Field(default="A", pattern="^(A|B|C|UNSPECIFIED)$")


class FPOIntakeRequest(BaseModel):
    member_id: str
    crop: str = Field(min_length=2, max_length=80)
    grade: str = Field(default="UNSPECIFIED", pattern="^(A|B|C|UNSPECIFIED)$")
    gross_quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    tare_quantity: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=3)
    unit: str = Field(default="kg", max_length=20)
    settlement_rate: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    notes: str | None = Field(default=None, max_length=1000)


class FPOMemberUpdateRequest(BaseModel):
    farmer_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=24)
    village: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    land_acres: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    primary_crop: str | None = Field(default=None, min_length=2, max_length=80)
    grade: str | None = Field(default=None, pattern="^(A|B|C|UNSPECIFIED)$")


class FPOPoolContributionRequest(BaseModel):
    intake_id: str
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)


class FPOIntakeCorrectionRequest(BaseModel):
    gross_quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    tare_quantity: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=3)
    reason: str = Field(min_length=3, max_length=500)


class FPOPoolCreateRequest(BaseModel):
    contributions: list[FPOPoolContributionRequest] = Field(min_length=1, max_length=200)


class FPOPoolPublishRequest(BaseModel):
    asking_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    location_text: str = Field(min_length=2, max_length=300)
    district: str | None = Field(default=None, max_length=100)


class FPOPoolContributionAddRequest(BaseModel):
    intake_id: str
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)


class FPOAggregateLotRequest(BaseModel):
    """Legacy payload retained only to return a safe migration message."""
    crop: str = Field(..., min_length=2, max_length=50)
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(default="quintal", max_length=20)
    grade: str = Field(default="A", max_length=10)
    asking_price: Decimal = Field(..., gt=0)
    location_text: str = Field(..., min_length=2)
    district: str | None = None
    member_ids: list[str] = Field(default_factory=list)
    notes: str | None = None
