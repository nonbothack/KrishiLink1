import uuid
from unittest.mock import Mock

from app.core.idempotency import _build_scoped_key, check_idempotency, save_idempotency
from app.models import IdempotencyKey


def test_scoped_idempotency_key_construction():
    req1 = Mock()
    req1.headers = {"Idempotency-Key": "same-key-123"}
    req1.url.path = "/api/v1/lots"
    req1.method = "POST"
    req1.state.user_id = "user-1"

    req2 = Mock()
    req2.headers = {"Idempotency-Key": "same-key-123"}
    req2.url.path = "/api/v1/lots"
    req2.method = "POST"
    req2.state.user_id = "user-2"

    key1 = _build_scoped_key(req1, user="user-1")
    key2 = _build_scoped_key(req2, user="user-2")

    # Keys must be distinct across different users despite same raw key string
    assert key1 == "user-1:POST:/api/v1/lots:same-key-123"
    assert key2 == "user-2:POST:/api/v1/lots:same-key-123"
    assert key1 != key2


def test_scoped_idempotency_db_isolation(db_session):
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())

    req1 = Mock()
    req1.headers = {"Idempotency-Key": "key-shared-uuid"}
    req1.url.path = "/api/v1/offers"
    req1.method = "POST"

    req2 = Mock()
    req2.headers = {"Idempotency-Key": "key-shared-uuid"}
    req2.url.path = "/api/v1/offers"
    req2.method = "POST"

    body1 = {"success": True, "data": {"offer_id": "offer-1", "user": user1_id}}
    body2 = {"success": True, "data": {"offer_id": "offer-2", "user": user2_id}}

    # Save for user 1
    save_idempotency(req1, db_session, 201, body1, user=user1_id)

    # Check for user 2: must be None because user 2 has not made this request
    cached_user2 = check_idempotency(req2, db_session, user=user2_id)
    assert cached_user2 is None

    # Check for user 1: must return cached response 1
    cached_user1 = check_idempotency(req1, db_session, user=user1_id)
    assert cached_user1 is not None
    assert cached_user1.response_body == body1

    # Save for user 2
    save_idempotency(req2, db_session, 201, body2, user=user2_id)
    cached_user2_after = check_idempotency(req2, db_session, user=user2_id)
    assert cached_user2_after is not None
    assert cached_user2_after.response_body == body2
