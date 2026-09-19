import asyncio
import hashlib
import uuid
from decimal import Decimal
from io import BytesIO

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

from app.core.evidence_files import MAX_EVIDENCE_SIZE_BYTES, read_validated_evidence
from app.models import (
    Evidence,
    Payment,
    StorageFacility,
    TradeEvent,
    TradeStorageRequest,
    TradeTermSnapshot,
    Transaction,
)


def create_trade(client, farmer_headers, buyer_headers, *, crop="Onion", quantity="40", price="2300"):
    lot_response = client.post(
        "/api/v1/lots",
        headers=farmer_headers,
        json={
            "crop": crop,
            "grade": "A",
            "quantity": quantity,
            "asking_price": price,
            "location_text": "Nashik collection point",
            "district": "Nashik",
        },
    )
    assert lot_response.status_code == 201, lot_response.text
    offer_response = client.post(
        "/api/v1/offers",
        headers=buyer_headers,
        json={"lot_id": lot_response.json()["data"]["id"], "quantity": quantity, "price_per_unit": price},
    )
    assert offer_response.status_code == 201, offer_response.text
    accepted = client.post(
        f"/api/v1/offers/{offer_response.json()['data']['id']}/accept",
        headers=farmer_headers,
    )
    assert accepted.status_code == 200, accepted.text
    return accepted.json()["data"]["transaction_id"]


def unrelated_buyer_headers(client):
    response = client.post("/api/v1/auth/login", json={"email": "mehta@demo.com", "password": "demo123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def test_payment_report_retry_is_idempotent_and_legacy_payment_is_not_claimed_as_report(
    client, db_session, auth_headers, buyer_auth_headers
):
    trade_id = create_trade(client, auth_headers, buyer_auth_headers)
    key = str(uuid.uuid4())
    headers = {**buyer_auth_headers, "Idempotency-Key": key}
    request = {"amount": "92000.00", "reference": "BUYER-ENTERED-REF-100"}

    first = client.post(f"/api/v1/trades/{trade_id}/payment-reports", headers=headers, json=request)
    second = client.post(f"/api/v1/trades/{trade_id}/payment-reports", headers=headers, json=request)
    assert first.status_code == second.status_code == 201
    assert first.json()["data"]["id"] == second.json()["data"]["id"]
    assert db_session.query(Payment).filter(Payment.transaction_id == uuid.UUID(trade_id)).count() == 1

    legacy = Payment(
        id=uuid.uuid4(), transaction_id=uuid.UUID(trade_id), provider="legacy", provider_reference="untrusted-old-ref",
        amount=Decimal("25.00"), currency="INR", status="PAID", source_kind="UNKNOWN_LEGACY",
    )
    db_session.add(legacy)
    db_session.commit()

    room_response = client.get(f"/api/v1/trades/{trade_id}/room", headers=buyer_auth_headers)
    assert room_response.status_code == 200
    payment_summary = room_response.json()["data"]["payment"]
    assert payment_summary["provider_connected"] is False
    assert payment_summary["provider_verified"] is False
    assert payment_summary["legacy_unverified_count"] == 1
    assert [item["reference"] for item in payment_summary["reports"]] == ["BUYER-ENTERED-REF-100"]
    assert payment_summary["reports"][0]["source_kind"] == "PARTICIPANT_REPORTED"
    assert room_response.json()["data"]["status"] == "CREATED"
    assert db_session.query(TradeEvent).filter(
        TradeEvent.transaction_id == uuid.UUID(trade_id), TradeEvent.event_type == "PAYMENT_REPORTED_SENT"
    ).count() == 1


def test_trade_room_get_does_not_invent_ids_terms_or_timeline_events(client, db_session, auth_headers, buyer_auth_headers):
    trade_id = create_trade(client, auth_headers, buyer_auth_headers)
    trade = db_session.get(Transaction, uuid.UUID(trade_id))
    assert trade is not None
    trade.public_id = None
    snapshot = db_session.query(TradeTermSnapshot).filter(TradeTermSnapshot.transaction_id == uuid.UUID(trade_id)).one()
    db_session.delete(snapshot)
    db_session.commit()
    before_events = db_session.query(TradeEvent).filter(TradeEvent.transaction_id == uuid.UUID(trade_id)).count()

    room = client.get(f"/api/v1/trades/{trade_id}/room", headers=buyer_auth_headers)
    listing = client.get("/api/v1/trades", headers=buyer_auth_headers)
    assert room.status_code == listing.status_code == 200
    assert room.json()["data"]["public_id"] is None
    assert room.json()["data"]["terms"] is None
    assert room.json()["data"]["payment"]["gross_value"] is None
    listed = next(item for item in listing.json()["data"]["items"] if item["id"] == trade_id)
    assert listed["public_id"] is None

    db_session.expire_all()
    assert db_session.get(Transaction, uuid.UUID(trade_id)).public_id is None
    assert db_session.query(TradeEvent).filter(TradeEvent.transaction_id == uuid.UUID(trade_id)).count() == before_events
    payment_report = client.post(
        f"/api/v1/trades/{trade_id}/payment-reports",
        headers={**buyer_auth_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"amount": "1.00", "reference": "no-terms"},
    )
    assert payment_report.status_code == 409


def test_quality_and_decimal_weighment_are_statements_not_assays_or_contract_changes(
    client, auth_headers, buyer_auth_headers
):
    trade_id = create_trade(client, auth_headers, buyer_auth_headers, quantity="20", price="2100")
    quality = client.post(
        f"/api/v1/trades/{trade_id}/quality-reports",
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"kind": "PARTICIPANT_CLAIM", "details": "The produce was sorted before dispatch.", "attributes": {"stage": "pickup"}},
    )
    assert quality.status_code == 201, quality.text

    weighment = client.post(
        f"/api/v1/trades/{trade_id}/weighments",
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"gross_quantity": "22.345", "tare_quantity": "0.125", "unit": "quintal"},
    )
    assert weighment.status_code == 201, weighment.text
    invalid_unit = client.post(
        f"/api/v1/trades/{trade_id}/weighments",
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"gross_quantity": "22.345", "tare_quantity": "0.125", "unit": "kg"},
    )
    invalid_weight = client.post(
        f"/api/v1/trades/{trade_id}/weighments",
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"gross_quantity": "1.000", "tare_quantity": "1.000", "unit": "quintal"},
    )
    assert invalid_unit.status_code == 422
    assert invalid_weight.status_code == 422

    room = client.get(f"/api/v1/trades/{trade_id}/room", headers=buyer_auth_headers).json()["data"]
    quality_event = next(event for event in room["timeline"] if event["event_type"] == "QUALITY_CLAIM")
    weight_event = next(event for event in room["timeline"] if event["event_type"] == "WEIGHMENT_REPORTED")
    assert quality_event["source_kind"] == "PARTICIPANT_REPORTED"
    assert quality_event["metadata"]["assay_verified"] is False
    assert room["quality"]["verification_status"] == "PARTICIPANT_REPORTED"
    assert weight_event["metadata"]["net_quantity"] == "22.220"
    assert weight_event["metadata"]["difference_quantity"] == "2.220"
    assert weight_event["metadata"]["calculation_source"] == "SERVER_DECIMAL"
    assert room["terms"]["quantity"] == 20.0


def test_storage_request_is_pending_and_idempotent_without_capacity_claim(
    client, db_session, auth_headers, buyer_auth_headers
):
    trade_id = create_trade(client, auth_headers, buyer_auth_headers, quantity="20")
    facility = StorageFacility(
        id=uuid.uuid4(), name="Reviewed facility", type="warehouse", location_text="Nashik",
        verification_status="VERIFIED", source_kind="REVIEWED_PARTNER", status="ACTIVE",
    )
    db_session.add(facility)
    db_session.commit()

    key = str(uuid.uuid4())
    headers = {**auth_headers, "Idempotency-Key": key}
    payload = {"facility_id": str(facility.id), "quantity": "12.500", "unit": "quintal"}
    first = client.post(f"/api/v1/trades/{trade_id}/storage-requests", headers=headers, json=payload)
    retry = client.post(f"/api/v1/trades/{trade_id}/storage-requests", headers=headers, json=payload)
    assert first.status_code == retry.status_code == 201
    assert first.json()["data"]["id"] == retry.json()["data"]["id"]
    assert db_session.query(TradeStorageRequest).filter(TradeStorageRequest.transaction_id == uuid.UUID(trade_id)).count() == 1

    room = client.get(f"/api/v1/trades/{trade_id}/room", headers=auth_headers).json()["data"]
    assert room["storage_requests"][0]["status"] == "REQUESTED"
    assert room["storage_requests"][0]["confirmation_status"] == "PENDING_FACILITY_CONFIRMATION"
    assert "capacity" not in room["storage_requests"][0]
    assert "rate" not in room["storage_requests"][0]


def test_trade_evidence_is_server_hashed_idempotent_and_participant_submitted(
    client, db_session, monkeypatch, auth_headers, buyer_auth_headers
):
    import app.modules.trades.service as trade_service

    uploaded = []
    monkeypatch.setattr(trade_service, "get_s3_client", lambda: object())
    monkeypatch.setattr(trade_service, "upload_file", lambda stream, key, mime: uploaded.append((stream.read(), key, mime)))
    monkeypatch.setattr(trade_service, "delete_file", lambda key: True)
    monkeypatch.setattr(trade_service, "generate_presigned_url", lambda key: "https://storage.invalid/signed")

    trade_id = create_trade(client, auth_headers, buyer_auth_headers)
    content = b"\x89PNG\r\n\x1a\n" + b"packet10-test-image"
    key = str(uuid.uuid4())
    headers = {**auth_headers, "Idempotency-Key": key}
    files = {"file": ("quality photo.png", content, "image/png")}
    data = {"classification": "QUALITY_PHOTO"}
    first = client.post(f"/api/v1/trades/{trade_id}/evidence", headers=headers, files=files, data=data)
    retry = client.post(f"/api/v1/trades/{trade_id}/evidence", headers=headers, files=files, data=data)
    assert first.status_code == retry.status_code == 201, first.text
    assert first.json()["data"]["evidence_id"] == retry.json()["data"]["evidence_id"]
    assert len(uploaded) == 1
    assert uploaded[0][0] == content
    assert uploaded[0][2] == "image/png"

    evidence = db_session.query(Evidence).filter(Evidence.transaction_id == uuid.UUID(trade_id)).one()
    assert evidence.uploader_id is not None
    assert evidence.classification == "QUALITY_PHOTO"
    assert evidence.provenance_status == "PARTICIPANT_SUBMITTED"
    assert evidence.file_hash == hashlib.sha256(content).hexdigest()
    assert evidence.file_size_bytes == len(content)
    assert evidence.original_filename == "quality_photo.png"
    room = client.get(f"/api/v1/trades/{trade_id}/room", headers=buyer_auth_headers).json()["data"]
    assert room["evidence"][0]["provenance_status"] == "PARTICIPANT_SUBMITTED"
    assert room["timeline"][-1]["event_type"] == "EVIDENCE_SUBMITTED"


def test_trade_grievance_is_authorized_and_uses_the_trade_timeline(
    client, auth_headers, buyer_auth_headers, admin_auth_headers
):
    trade_id = create_trade(client, auth_headers, buyer_auth_headers)
    unrelated_headers = unrelated_buyer_headers(client)
    denied = client.post(
        "/api/v1/disputes",
        headers=unrelated_headers,
        json={"transaction_id": trade_id, "reason": "Unrelated dispute", "description": "Not a trade participant."},
    )
    assert denied.status_code == 403

    opened = client.post(
        "/api/v1/disputes",
        headers=auth_headers,
        json={"transaction_id": trade_id, "reason": "Quality concern", "description": "The grade needs review."},
    )
    assert opened.status_code == 201, opened.text
    dispute_id = opened.json()["data"]["id"]
    assert client.get(f"/api/v1/disputes/{dispute_id}", headers=unrelated_headers).status_code == 403

    reviewed = client.post(
        f"/api/v1/disputes/{dispute_id}/status",
        headers=admin_auth_headers,
        json={"status": "UNDER_REVIEW"},
    )
    assert reviewed.status_code == 200
    room = client.get(f"/api/v1/trades/{trade_id}/room", headers=buyer_auth_headers).json()["data"]
    assert room["status"] == "DISPUTED"
    assert [event["event_type"] for event in room["timeline"]][-2:] == ["DISPUTE_OPENED", "DISPUTE_STATUS_CHANGED"]


def test_evidence_reader_rejects_mismatched_and_oversized_uploads():
    mismatched = UploadFile(
        filename="fake.png", file=BytesIO(b"not a png"), headers=Headers({"content-type": "image/png"})
    )
    with pytest.raises(HTTPException) as mismatch_error:
        asyncio.run(read_validated_evidence(mismatched))
    assert mismatch_error.value.status_code == 400

    oversized = UploadFile(
        filename="large.pdf",
        file=BytesIO(b"%PDF-" + b"x" * MAX_EVIDENCE_SIZE_BYTES),
        headers=Headers({"content-type": "application/pdf"}),
    )
    with pytest.raises(HTTPException) as size_error:
        asyncio.run(read_validated_evidence(oversized))
    assert size_error.value.status_code == 413


def test_legacy_client_supplied_evidence_key_is_authorized_then_rejected(client, auth_headers, buyer_auth_headers):
    dispute = client.post(
        "/api/v1/disputes",
        headers=auth_headers,
        json={"reason": "Trade evidence", "description": "This needs supporting material."},
    ).json()["data"]
    payload = {"s3_key": "arbitrary/client/key", "file_hash": "0" * 64, "mime_type": "image/png"}
    unauthorized = client.post(
        f"/api/v1/disputes/{dispute['id']}/evidence", headers=buyer_auth_headers, json=payload
    )
    owner = client.post(f"/api/v1/disputes/{dispute['id']}/evidence", headers=auth_headers, json=payload)
    assert unauthorized.status_code == 403
    assert owner.status_code == 410
