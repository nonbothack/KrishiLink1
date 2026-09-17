import uuid
import pytest
from fastapi.testclient import TestClient

def test_register(client):
    unique_email = f"test-register-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "Test1234!",
        "full_name": "Test User",
        "role": "buyer",
    })
    assert r.status_code == 201
    data = r.json()["data"]
    assert "user" in data
    assert "access_token" in data
    assert data["user"]["email"] == unique_email

def test_login(client, ensure_test_users):
    r = client.post("/api/v1/auth/login", json={
        "email": "ramesh@demo.com",
        "password": "demo123!",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "ramesh@demo.com"

def test_login_invalid_password(client, ensure_test_users):
    r = client.post("/api/v1/auth/login", json={
        "email": "ramesh@demo.com",
        "password": "wrongpassword",
    })
    assert r.status_code == 401

def test_me(client, auth_headers):
    r = client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["success"] == True
    assert r.json()["data"]["email"] == "ramesh@demo.com"

def test_me_invalid_token(client):
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert r.status_code == 401

def test_refresh(client, ensure_test_users):
    r = client.post("/api/v1/auth/login", json={"email": "ramesh@demo.com", "password": "demo123!"})
    assert r.status_code == 200
    refresh_token = r.json()["data"]["refresh_token"]
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r2.status_code == 200
    assert "access_token" in r2.json()["data"]


def test_web_session_uses_http_only_cookie_and_logout_revokes_it(client, ensure_test_users):
    web_headers = {"X-KrishiLink-Client": "web", "Origin": "http://localhost:5173"}
    login = client.post(
        "/api/v1/auth/login",
        headers=web_headers,
        json={"email": "ramesh@demo.com", "password": "demo123!"},
    )
    assert login.status_code == 200
    assert "refresh_token" not in login.json()["data"]
    assert "HttpOnly" in login.headers["set-cookie"]

    refresh = client.post("/api/v1/auth/refresh", headers=web_headers)
    assert refresh.status_code == 200
    access_token = refresh.json()["data"]["access_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        headers={**web_headers, "Authorization": f"Bearer {access_token}"},
    )
    assert logout.status_code == 200

    revoked = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert revoked.status_code == 401

def test_logout(client, auth_headers):
    r = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["success"] == True

def test_forgot_and_reset_password(client, ensure_test_users):
    # Request reset
    r = client.post("/api/v1/auth/forgot-password", json={"email": "ramesh@demo.com"})
    assert r.status_code == 200
    assert r.json()["success"] == True
    token = r.json()["data"].get("dev_reset_token")
    assert token is not None

    # Reset with new password
    r2 = client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": "NewSecret123!"
    })
    assert r2.status_code == 200
    assert r2.json()["success"] == True

    # Verify login with new password
    r3 = client.post("/api/v1/auth/login", json={
        "email": "ramesh@demo.com",
        "password": "NewSecret123!"
    })
    assert r3.status_code == 200

    # Reset back to demo123! for other tests
    r4 = client.post("/api/v1/auth/forgot-password", json={"email": "ramesh@demo.com"})
    tok = r4.json()["data"].get("dev_reset_token")
    client.post("/api/v1/auth/reset-password", json={"token": tok, "new_password": "demo123!"})
