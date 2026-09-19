import pytest
import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from app.models import Crop, DataSourceRegistry, Lot, Market, Offer, PriceObservation, PriceSource, User
from app.modules.lots.service import calculate_farmer_earnings
from app.modules.markets.service import ensure_agmarknet_source
from app.modules.prices.provider import PARSER_VERSION

@pytest.fixture
def mock_farmer_id(db_session, ensure_test_users):
    farmer = db_session.query(User).filter(User.email == "ramesh@demo.com").first()
    return str(farmer.id)

@pytest.fixture
def mock_buyer_id(db_session, ensure_test_users):
    buyer = db_session.query(User).filter(User.email == "buyer@demo.com").first()
    return str(buyer.id)


def record_official_price(db_session, *, price=2800):
    crop = Crop(
        id=uuid.uuid4(), name=f"Packet06 Wheat {uuid.uuid4().hex[:8]}",
        category="test", unit="quintal", valid_units=["quintal"],
    )
    db_session.add(crop)
    db_session.flush()
    market = db_session.query(Market).filter(Market.name == "Nashik APMC").first()
    registry = ensure_agmarknet_source(db_session, PARSER_VERSION)
    source = PriceSource(
        id=uuid.uuid4(), name=f"Packet06 AGMARKNET {uuid.uuid4().hex}",
        adapter=PARSER_VERSION, registry_id=registry.id, is_active=True,
    )
    db_session.add(source)
    db_session.flush()
    db_session.add(PriceObservation(
        id=uuid.uuid4(), crop_id=crop.id, market_id=market.id, price_date=date.today(),
        min_price=Decimal(str(price - 100)), modal_price=Decimal(str(price)),
        max_price=Decimal(str(price + 100)), price_unit="INR/quintal", source_id=source.id,
        parser_version=PARSER_VERSION, observation_key=f"packet06:{uuid.uuid4()}", quality_status="HIGH",
    ))
    db_session.flush()
    return crop

def test_calculate_farmer_earnings_success(db_session, mock_farmer_id, mock_buyer_id):
    crop = record_official_price(db_session)
    lot_id = uuid.uuid4()
    lot = Lot(
        id=lot_id,
        public_id=f"KL-LOT-{uuid.uuid4().hex[:10]}",
        owner_id=uuid.UUID(mock_farmer_id),
        crop_id=crop.id,
        crop_name=crop.name,
        grade="A",
        quantity=Decimal("100"),
        market_reference_price=Decimal("2800"),
        location_text="Test Loc"
    )
    db_session.add(lot)
    
    offer1 = Offer(
        id=uuid.uuid4(),
        lot_id=lot_id,
        buyer_id=uuid.UUID(mock_buyer_id),
        owner_id=uuid.UUID(mock_farmer_id),
        status="PENDING",
        quantity=Decimal("100"),
        price_per_unit=Decimal("3100"),
    )
    offer2 = Offer(
        id=uuid.uuid4(),
        lot_id=lot_id,
        buyer_id=uuid.UUID(mock_buyer_id),
        owner_id=uuid.UUID(mock_farmer_id),
        status="PENDING",
        quantity=Decimal("50"),
        price_per_unit=Decimal("3000"),
    )
    db_session.add(offer1)
    db_session.add(offer2)
    db_session.commit()
    
    result = calculate_farmer_earnings(db_session, str(lot_id), mock_farmer_id)
    assert result["market_value"] == 280000.0
    assert result["best_offer_value"] == 310000.0
    assert result["potential_additional_earnings"] == 30000.0

def test_calculate_farmer_earnings_no_offer(db_session, mock_farmer_id):
    crop = record_official_price(db_session)
    lot_id = uuid.uuid4()
    lot = Lot(
        id=lot_id,
        public_id=f"KL-LOT-{uuid.uuid4().hex[:10]}",
        owner_id=uuid.UUID(mock_farmer_id),
        crop_id=crop.id,
        crop_name=crop.name,
        grade="A",
        quantity=Decimal("100"),
        market_reference_price=Decimal("2800"),
        location_text="Test Loc"
    )
    db_session.add(lot)
    db_session.commit()
    
    with pytest.raises(ValueError, match="Lot has no buyer offers"):
        calculate_farmer_earnings(db_session, str(lot_id), mock_farmer_id)

def test_calculate_farmer_earnings_missing_market_price(db_session, mock_farmer_id):
    crop = Crop(
        id=uuid.uuid4(), name=f"Packet06 No Price {uuid.uuid4().hex[:8]}",
        category="test", unit="quintal", valid_units=["quintal"],
    )
    db_session.add(crop)
    db_session.flush()
    lot_id = uuid.uuid4()
    lot = Lot(
        id=lot_id,
        public_id=f"KL-LOT-{uuid.uuid4().hex[:10]}",
        owner_id=uuid.UUID(mock_farmer_id),
        crop_id=crop.id,
        crop_name=crop.name,
        grade="A",
        quantity=Decimal("100"),
        market_reference_price=None,
        location_text="Test Loc"
    )
    db_session.add(lot)
    db_session.commit()
    
    with pytest.raises(ValueError, match="No recent official comparable market price"):
        calculate_farmer_earnings(db_session, str(lot_id), mock_farmer_id)

def test_calculate_farmer_earnings_invalid_quantity(db_session, mock_farmer_id):
    crop = record_official_price(db_session)
    lot_id = uuid.uuid4()
    lot = Lot(
        id=lot_id,
        public_id=f"KL-LOT-{uuid.uuid4().hex[:10]}",
        owner_id=uuid.UUID(mock_farmer_id),
        crop_id=crop.id,
        crop_name=crop.name,
        grade="A",
        quantity=Decimal("100"),
        market_reference_price=Decimal("2800"),
        location_text="Test Loc"
    )
    db_session.add(lot)
    db_session.commit()
    
    lot.quantity = Decimal("0")
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
        
def test_calculate_farmer_earnings_wrong_farmer(db_session, mock_farmer_id):
    crop = record_official_price(db_session)
    lot_id = uuid.uuid4()
    lot = Lot(
        id=lot_id,
        public_id=f"KL-LOT-{uuid.uuid4().hex[:10]}",
        owner_id=uuid.UUID(mock_farmer_id),
        crop_id=crop.id,
        crop_name=crop.name,
        grade="A",
        quantity=Decimal("100"),
        market_reference_price=Decimal("2800"),
        location_text="Test Loc"
    )
    db_session.add(lot)
    db_session.commit()
    
    other_farmer_id = str(uuid.uuid4())
    with pytest.raises(ValueError, match="Farmer doesn't own the lot"):
        calculate_farmer_earnings(db_session, str(lot_id), other_farmer_id)

def test_calculate_farmer_earnings_lot_not_exist(db_session):
    with pytest.raises(ValueError, match="Lot doesn't exist"):
        calculate_farmer_earnings(db_session, str(uuid.uuid4()), str(uuid.uuid4()))

def test_calculate_farmer_earnings_invalid_price(db_session, mock_farmer_id):
    crop = Crop(
        id=uuid.uuid4(), name=f"Packet06 Invalid Price {uuid.uuid4().hex[:8]}",
        category="test", unit="quintal", valid_units=["quintal"],
    )
    db_session.add(crop)
    db_session.flush()
    lot_id = uuid.uuid4()
    lot = Lot(
        id=lot_id,
        public_id=f"KL-LOT-{uuid.uuid4().hex[:10]}",
        owner_id=uuid.UUID(mock_farmer_id),
        crop_id=crop.id,
        crop_name=crop.name,
        grade="A",
        quantity=Decimal("100"),
        market_reference_price=Decimal("0"),
        location_text="Test Loc"
    )
    db_session.add(lot)
    db_session.commit()
    
    with pytest.raises(ValueError, match="No recent official comparable market price"):
        calculate_farmer_earnings(db_session, str(lot_id), mock_farmer_id)
