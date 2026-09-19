import uuid


def test_register(client):
    unique_email = f"test-register-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "Test1234!x",
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

    csrf_token = login.cookies.get("krishilink_csrf")
    assert csrf_token
    refresh = client.post(
        "/api/v1/auth/refresh",
        headers={**web_headers, "X-KrishiLink-CSRF": csrf_token},
    )
    assert refresh.status_code == 200
    access_token = refresh.json()["data"]["access_token"]
    csrf_token = refresh.cookies.get("krishilink_csrf", csrf_token)

    logout = client.post(
        "/api/v1/auth/logout",
        headers={
            **web_headers,
            "Authorization": f"Bearer {access_token}",
            "X-KrishiLink-CSRF": csrf_token,
        },
    )
    assert logout.status_code == 200

    revoked = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert revoked.status_code == 401


def test_web_session_rejects_refresh_and_logout_without_csrf_header(client, ensure_test_users):
    web_headers = {"X-KrishiLink-Client": "web", "Origin": "http://localhost:5173"}
    login = client.post(
        "/api/v1/auth/login",
        headers=web_headers,
        json={"email": "ramesh@demo.com", "password": "demo123!"},
    )
    assert login.status_code == 200
    access_token = login.json()["data"]["access_token"]
    refresh = client.post("/api/v1/auth/refresh", headers=web_headers)
    assert refresh.status_code == 403
    logout = client.post(
        "/api/v1/auth/logout",
        headers={**web_headers, "Authorization": f"Bearer {access_token}"},
    )
    assert logout.status_code == 403

def test_logout(client, auth_headers):
    r = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["success"] == True

def test_logout_revokes_tokens(client, ensure_test_users):
    # 1. Login to get fresh tokens
    r_login = client.post("/api/v1/auth/login", json={"email": "ramesh@demo.com", "password": "demo123!"})
    assert r_login.status_code == 200
    access_tok = r_login.json()["data"]["access_token"]
    refresh_tok = r_login.json()["data"]["refresh_token"]

    # 2. Access /auth/me with active token -> 200
    r_me1 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_tok}"})
    assert r_me1.status_code == 200

    # 3. Logout providing access token and refresh token
    r_logout = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_tok}"},
        json={"refresh_token": refresh_tok},
    )
    assert r_logout.status_code == 200

    # 4. Accessing /auth/me with revoked access token must now be 401
    r_me2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_tok}"})
    assert r_me2.status_code == 401
    assert r_me2.status_code == 401

    # 5. Using revoked refresh token must now be 401
    r_ref = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_tok})
    assert r_ref.status_code == 401
    assert r_ref.status_code == 401

def test_forgot_and_reset_password(client, ensure_test_users, db_session):
    from app.models import OutboxEvent
    previous_event_ids = {
        event.id for event in db_session.query(OutboxEvent).filter(OutboxEvent.event_type == "user.password_reset_requested")
    }
    # Request reset
    r = client.post("/api/v1/auth/forgot-password", json={"email": "ramesh@demo.com"})
    assert r.status_code == 200
    assert r.json()["success"] == True
    token = r.json()["data"].get("dev_reset_token")
    assert token is not None
    reset_events = [
        event for event in db_session.query(OutboxEvent).filter(OutboxEvent.event_type == "user.password_reset_requested")
        if event.id not in previous_event_ids
    ]
    assert reset_events
    assert all("token" not in event.payload for event in reset_events)
    assert all(token not in str(event.payload) for event in reset_events)

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

    # Restore the legacy demo fixture directly; password reset correctly enforces
    # the new minimum length, while older seeded demo credentials remain usable.
    from app.core.security import hash_password
    from app.models import User

    user = db_session.query(User).filter(User.email == "ramesh@demo.com").one()
    user.password_hash = hash_password("demo123!")
    db_session.commit()
