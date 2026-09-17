import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.main import app
from app.models import Crop, Market, User


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def ensure_test_users():
    Base.metadata.create_all(engine)
    if "sqlite" in str(engine.url):
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE transactions ADD COLUMN public_id TEXT"))
                conn.commit()
            except Exception:
                pass
    db = SessionLocal()
    try:
        # Seed test crops
        crops_to_seed = [
            ("Wheat", "गहू", "Cereal", "quintal"),
            ("Onion", "कांदा", "Vegetable", "quintal"),
            ("Tomato", "टोमॅटो", "Vegetable", "quintal"),
            ("Soybean", "सोयाबीन", "Oilseed", "quintal"),
        ]
        for name, mr, cat, unit in crops_to_seed:
            c = db.query(Crop).filter(Crop.name.ilike(name)).first()
            if not c:
                db.add(Crop(id=uuid.uuid4(), name=name, name_marathi=mr, category=cat, unit=unit))

        # Seed test markets
        markets_to_seed = [
            ("Nashik APMC", "Nashik", "Maharashtra"),
            ("Lasalgaon APMC", "Nashik", "Maharashtra"),
            ("Pune APMC", "Pune", "Maharashtra"),
        ]
        for mname, dist, state in markets_to_seed:
            m = db.query(Market).filter(Market.name == mname).first()
            if not m:
                db.add(Market(id=uuid.uuid4(), name=mname, district=dist, state=state, is_active=True))

        # Seed test users
        users_to_ensure = [
            ("ramesh@demo.com", "9876543210", "Ramesh Patil", "farmer", "Nashik, Maharashtra", "Nashik"),
            ("buyer@demo.com", "9876543211", "Sunil Mehta", "buyer", "Mumbai, Maharashtra", "Mumbai"),
            ("mehta@demo.com", "9876543212", "Mehta Traders", "buyer", "Nashik, Maharashtra", "Nashik"),
            ("admin@demo.com", "9876543213", "Admin User", "admin", "Mumbai, Maharashtra", "Mumbai"),
            ("fpo@demo.com", "9876543214", "Nashik Farmers Collective", "fpo", "Nashik, Maharashtra", "Nashik"),
        ]

        for email, phone, name, role, loc, dist in users_to_ensure:
            u = db.query(User).filter(User.email == email).first()
            if not u:
                u = User(
                    id=uuid.uuid4(),
                    email=email,
                    phone=phone,
                    full_name=name,
                    password_hash=hash_password("demo123!"),
                    role=role,
                    location=loc,
                    district=dist,
                    state="Maharashtra",
                    is_verified=True,
                    is_active=True
                )
                db.add(u)
            else:
                u.password_hash = hash_password("demo123!")
                u.is_active = True

        db.commit()
    finally:
        db.close()

@pytest.fixture
def auth_headers(client, ensure_test_users):
    r = client.post("/api/v1/auth/login", json={"email": "ramesh@demo.com", "password": "demo123!"})
    if r.status_code != 200:
        pytest.fail(f"Cannot authenticate test farmer user: {r.text}")
    data = r.json()["data"]
    return {"Authorization": f"Bearer {data['access_token']}"}

@pytest.fixture
def buyer_auth_headers(client, ensure_test_users):
    r = client.post("/api/v1/auth/login", json={"email": "buyer@demo.com", "password": "demo123!"})
    if r.status_code != 200:
        pytest.fail(f"Cannot authenticate test buyer user: {r.text}")
    data = r.json()["data"]
    return {"Authorization": f"Bearer {data['access_token']}"}

@pytest.fixture
def admin_auth_headers(client, ensure_test_users):
    r = client.post("/api/v1/auth/login", json={"email": "admin@demo.com", "password": "demo123!"})
    if r.status_code != 200:
        pytest.fail(f"Cannot authenticate test admin user: {r.text}")
    data = r.json()["data"]
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest.fixture
def fpo_auth_headers(client, ensure_test_users):
    r = client.post("/api/v1/auth/login", json={"email": "fpo@demo.com", "password": "demo123!"})
    if r.status_code != 200:
        pytest.fail(f"Cannot authenticate test fpo user: {r.text}")
    data = r.json()["data"]
    return {"Authorization": f"Bearer {data['access_token']}"}
