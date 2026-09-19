import pytest

from app.core.domain_contracts import (
    GRIEVANCE_TRANSITIONS,
    LOT_TRANSITIONS,
    NOTIFICATION_ATTEMPT_TRANSITIONS,
    OFFER_TRANSITIONS,
    PAYMENT_ATTEMPT_TRANSITIONS,
    STORAGE_BOOKING_TRANSITIONS,
    TRADE_TRANSITIONS,
    VERIFICATION_CASE_TRANSITIONS,
    transition_allowed,
)


@pytest.mark.parametrize(
    ("graph", "current", "target"),
    [
        (LOT_TRANSITIONS, "SOLD", "PUBLISHED"),
        (OFFER_TRANSITIONS, "ACCEPTED", "PENDING"),
        (TRADE_TRANSITIONS, "COMPLETED", "PAYMENT_PENDING"),
        (STORAGE_BOOKING_TRANSITIONS, "CHECKED_OUT", "CONFIRMED"),
        (VERIFICATION_CASE_TRANSITIONS, "APPROVED", "PENDING"),
        (GRIEVANCE_TRANSITIONS, "RESOLVED", "OPEN"),
        (PAYMENT_ATTEMPT_TRANSITIONS, "SUCCEEDED", "FAILED"),
        (NOTIFICATION_ATTEMPT_TRANSITIONS, "DELIVERED", "PENDING"),
    ],
)
def test_domain_graphs_reject_illegal_terminal_transitions(graph, current, target):
    assert not transition_allowed(current, target, graph)


def test_shared_trade_contract_rejects_skips_and_terminal_reopens():
    assert transition_allowed("CREATED", "PAYMENT_PENDING", TRADE_TRANSITIONS)
    assert not transition_allowed("CREATED", "PAYMENT_CONFIRMED", TRADE_TRANSITIONS)
    assert not transition_allowed("CREATED", "COMPLETED", TRADE_TRANSITIONS)
    assert not transition_allowed("COMPLETED", "PAYMENT_PENDING", TRADE_TRANSITIONS)
    assert not transition_allowed("UNKNOWN", "COMPLETED", TRADE_TRANSITIONS)


def test_trade_apis_enforce_same_transition_graph(client, auth_headers, buyer_auth_headers, admin_auth_headers):
    lot = client.post(
        "/api/v1/lots",
        json={"crop": "Wheat", "grade": "A", "quantity": 12, "asking_price": 2100, "location_text": "Farm"},
        headers=auth_headers,
    ).json()["data"]["id"]
    offer = client.post(
        "/api/v1/offers", json={"lot_id": lot, "quantity": 8, "price_per_unit": 2100}, headers=buyer_auth_headers
    ).json()["data"]["id"]
    accepted = client.post(f"/api/v1/offers/{offer}/accept", headers=auth_headers).json()["data"]
    transaction_id = accepted["transaction_id"]

    legacy_api = client.post(
        f"/api/v1/transactions/{transaction_id}/transition",
        headers=buyer_auth_headers,
        json={"to_status": "COMPLETED"},
    )
    trade_api = client.post(
        f"/api/v1/trades/{transaction_id}/transition",
        headers=admin_auth_headers,
        json={"to_status": "COMPLETED"},
    )
    assert legacy_api.status_code == 409
    assert trade_api.status_code == 409

    room = client.get(f"/api/v1/trades/{transaction_id}/room", headers=buyer_auth_headers).json()["data"]
    assert room["status"] == "CREATED"


def test_grievance_contract_rejects_unknown_and_terminal_reopen(client, auth_headers, admin_auth_headers):
    assert transition_allowed("OPEN", "UNDER_REVIEW", GRIEVANCE_TRANSITIONS)
    assert not transition_allowed("RESOLVED", "OPEN", GRIEVANCE_TRANSITIONS)

    created = client.post(
        "/api/v1/disputes",
        headers=auth_headers,
        json={"reason": "Test grievance", "description": "Testing lifecycle contract."},
    ).json()["data"]
    dispute_id = created["id"]

    invalid = client.post(
        f"/api/v1/disputes/{dispute_id}/status",
        headers=admin_auth_headers,
        json={"status": "NOT_A_STATUS"},
    )
    assert invalid.status_code == 409

    resolved = client.post(
        f"/api/v1/disputes/{dispute_id}/status",
        headers=admin_auth_headers,
        json={"status": "RESOLVED", "resolution": "Reviewed"},
    )
    assert resolved.status_code == 200

    reopen = client.post(
        f"/api/v1/disputes/{dispute_id}/status",
        headers=admin_auth_headers,
        json={"status": "OPEN"},
    )
    assert reopen.status_code == 409
