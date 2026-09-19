"""Packet 08A operational conservation, ownership and interoperability contracts."""

import uuid
from decimal import Decimal

from app.core.security import hash_password
from app.models import (
    AuditLog,
    Crop,
    FPOPool,
    FPOIntake,
    FPOMember,
    FPOMemberTradeAllocation,
    FPOPoolContribution,
    Offer,
    Transaction,
    Lot,
    Reservation,
    User,
)


def _crop(db, valid_units=None):
    crop = Crop(id=uuid.uuid4(), name=f"FPO crop {uuid.uuid4().hex[:8]}", category="test", unit="quintal",
                valid_units=valid_units or ["quintal", "kg"], is_active=True, is_tradable=True)
    db.add(crop); db.commit(); return crop


def _member(client, headers, name="Asha Member", code=None, phone=None):
    payload = {"farmer_name": name, "primary_crop": "Onion", "grade": "A"}
    if phone:
        payload["phone"] = phone
    if code:
        payload["member_code"] = code
    response = client.post("/api/v1/fpo/members", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _intake(client, headers, member_id, crop, quantity="1000", unit="kg", tare="0", key=None, grade="A"):
    payload = {"member_id": member_id, "crop": str(crop.id), "grade": grade,
               "gross_quantity": quantity, "tare_quantity": tare, "unit": unit}
    headers = {**headers, **({"Idempotency-Key": key} if key else {})}
    return client.post("/api/v1/fpo/intakes", headers=headers, json=payload)


def _pool(client, headers, contributions, extra=None):
    payload = {"contributions": [{"intake_id": iid, "quantity": str(amount)} for iid, amount in contributions]}
    if extra:
        payload.update(extra)
    response = client.post("/api/v1/fpo/pools", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _publish(client, headers, pool, price="2500"):
    response = client.post(f"/api/v1/fpo/pools/{pool['id']}/publish", headers=headers,
                           json={"asking_price": price, "location_text": "Nashik District", "district": "Nashik"})
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _offer(client, buyer_headers, lot, quantity, price="2500", key=None):
    headers = {**buyer_headers, **({"Idempotency-Key": key} if key else {})}
    response = client.post("/api/v1/offers", headers=headers,
        json={"lot_id": lot["id"], "quantity": str(quantity), "unit": "quintal", "price_per_unit": str(price)})
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _other_fpo(client, db):
    email = f"fpo-08-{uuid.uuid4().hex[:8]}@example.test"
    db.add(User(id=uuid.uuid4(), email=email, phone=f"7{uuid.uuid4().int % 10**9:09d}", full_name="Other FPO",
                password_hash=hash_password("packet08-password"), role="fpo", is_active=True))
    db.commit()
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "packet08-password"})
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def test_intake_calculates_net_canonical_quantity_and_is_idempotent(client, fpo_auth_headers, db_session):
    crop = _crop(db_session); member = _member(client, fpo_auth_headers)
    response = _intake(client, fpo_auth_headers, member["id"], crop, "1100.000", "kg", "100.000", str(uuid.uuid4()))
    assert response.status_code == 201, response.text
    receipt = response.json()["data"]
    assert receipt["gross_quantity"] == "1100.000" and receipt["tare_quantity"] == "100.000"
    assert receipt["net_quantity"] == "1000.000" and receipt["unit"] == "kg"
    assert receipt["canonical_quantity_qtl"] == "10.000"
    persisted = db_session.get(FPOIntake, uuid.UUID(receipt["id"]))
    assert persisted is not None
    assert persisted.gross_quantity == Decimal("1100.000") and persisted.net_quantity == Decimal("1000.000")
    assert persisted.unit == "kg" and persisted.canonical_quantity == Decimal("10.000")
    duplicate_key = str(uuid.uuid4())
    first = _intake(client, fpo_auth_headers, member["id"], crop, "1000", key=duplicate_key)
    again = _intake(client, fpo_auth_headers, member["id"], crop, "1000", key=duplicate_key)
    assert first.status_code == 201 and again.status_code == 201
    assert first.json()["data"]["id"] == again.json()["data"]["id"]
    assert db_session.query(FPOIntake).filter(FPOIntake.id == uuid.UUID(first.json()["data"]["id"])).count() == 1


def test_intake_rejects_invalid_net_and_unsupported_unit(client, fpo_auth_headers, db_session):
    crop = _crop(db_session, ["quintal", "kg"]); member = _member(client, fpo_auth_headers)
    assert _intake(client, fpo_auth_headers, member["id"], crop, "10", "kg", "11").status_code == 422
    assert _intake(client, fpo_auth_headers, member["id"], crop, "10", "kg", "10").status_code == 422
    assert _intake(client, fpo_auth_headers, member["id"], crop, "10", "tonne").status_code == 422


def test_intake_conserves_across_multiple_pools_and_rejects_overallocation(client, fpo_auth_headers, db_session):
    crop = _crop(db_session); member = _member(client, fpo_auth_headers)
    intake = _intake(client, fpo_auth_headers, member["id"], crop).json()["data"]
    first = _pool(client, fpo_auth_headers, [(intake["id"], "6.000")])
    second = _pool(client, fpo_auth_headers, [(intake["id"], "2.000")])
    assert first["quantity_qtl"] == "6.000" and second["quantity_qtl"] == "2.000"
    assert sum((row.quantity for row in db_session.query(FPOPoolContribution).filter(FPOPoolContribution.intake_id == uuid.UUID(intake["id"])).all()), Decimal("0")) == Decimal("8.000")
    current = client.get(f"/api/v1/fpo/intakes/{intake['id']}/receipt", headers=fpo_auth_headers).json()["data"]
    assert current["available_quantity_qtl"] == "2.000"
    assert client.post("/api/v1/fpo/pools", headers=fpo_auth_headers, json={"contributions": [{"intake_id": intake["id"], "quantity": "3"}]}).status_code == 409


def test_pool_total_is_server_sum_for_multiple_members_and_receipts(client, fpo_auth_headers, db_session):
    crop = _crop(db_session); entries = []
    for name, amount in (("Member A", "4"), ("Member B", "7"), ("Member C", "9")):
        member = _member(client, fpo_auth_headers, name)
        receipt = _intake(client, fpo_auth_headers, member["id"], crop, amount, "quintal").json()["data"]
        entries.append((receipt["id"], amount))
    pool = _pool(client, fpo_auth_headers, entries, extra={"quantity": "999999"})
    contributions = db_session.query(FPOPoolContribution).filter(FPOPoolContribution.pool_id == uuid.UUID(pool["id"])).all()
    assert pool["quantity_qtl"] == "20.000"
    assert sum((row.quantity for row in contributions), Decimal("0")) == Decimal("20.000")


def test_published_pool_contribution_cannot_be_added_removed_or_corrected(client, fpo_auth_headers, db_session):
    crop = _crop(db_session); member = _member(client, fpo_auth_headers); receipt = _intake(client, fpo_auth_headers, member["id"], crop, "10", "quintal").json()["data"]
    pool = _pool(client, fpo_auth_headers, [(receipt["id"], "10")]); lot = _publish(client, fpo_auth_headers, pool)
    contribution = db_session.query(FPOPoolContribution).filter_by(pool_id=uuid.UUID(pool["id"])).one()
    assert client.post(f"/api/v1/fpo/pools/{pool['id']}/contributions", headers=fpo_auth_headers, json={"intake_id": receipt["id"], "quantity": "1"}).status_code == 409
    assert client.delete(f"/api/v1/fpo/pools/{pool['id']}/contributions/{contribution.id}", headers=fpo_auth_headers).status_code == 409
    assert client.post(f"/api/v1/fpo/intakes/{receipt['id']}/corrections", headers=fpo_auth_headers, json={"gross_quantity": "9", "tare_quantity": "0", "reason": "Correction"}).status_code == 409
    assert client.patch(f"/api/v1/lots/{lot['id']}", headers=fpo_auth_headers, json={"quantity": "9"}).status_code == 409


def test_fpo_lot_withdrawal_preserves_pool_ledger_and_marks_pool_withdrawn(client, fpo_auth_headers, db_session):
    crop = _crop(db_session); member = _member(client, fpo_auth_headers)
    receipt = _intake(client, fpo_auth_headers, member["id"], crop, "10", "quintal").json()["data"]
    pool = _pool(client, fpo_auth_headers, [(receipt["id"], "10")]); lot = _publish(client, fpo_auth_headers, pool)
    response = client.post(f"/api/v1/lots/{lot['id']}/withdraw", headers=fpo_auth_headers)
    assert response.status_code == 200 and response.json()["data"]["status"] == "CANCELLED"
    persisted_pool = db_session.get(FPOPool, uuid.UUID(pool["id"]))
    contribution = db_session.query(FPOPoolContribution).filter_by(pool_id=uuid.UUID(pool["id"])).one()
    assert persisted_pool.status == "WITHDRAWN" and contribution.quantity == Decimal("10.000")


def test_fpo_direct_lot_cannot_bypass_pools_and_untraced_legacy_lot_cannot_be_sold(
    client, fpo_auth_headers, buyer_auth_headers, db_session
):
    crop = _crop(db_session)
    direct = client.post("/api/v1/lots", headers=fpo_auth_headers, json={
        "crop": str(crop.id), "quantity": "5", "unit": "quintal", "asking_price": "100", "location_text": "Nashik",
    })
    assert direct.status_code == 409
    owner = db_session.query(User).filter_by(email="fpo@demo.com").one()
    legacy_lot = Lot(id=uuid.uuid4(), public_id=f"KL-LOT-LEGACY-{uuid.uuid4().hex[:8]}", owner_id=owner.id,
        crop_id=crop.id, crop_name=crop.name, grade="A", quantity=Decimal("5.00"), unit="quintal",
        asking_price=Decimal("100.00"), location_text="Nashik", status="PUBLISHED")
    db_session.add(legacy_lot); db_session.commit()
    offer = _offer(client, buyer_auth_headers, {"id": str(legacy_lot.id)}, "2", "100")
    accepted = client.post(f"/api/v1/offers/{offer['id']}/accept", headers=fpo_auth_headers)
    assert accepted.status_code == 409
    assert db_session.query(Transaction).filter(Transaction.lot_id == legacy_lot.id).count() == 0
    assert db_session.get(Offer, uuid.UUID(offer["id"])).status == "PENDING"


def test_partial_sales_reconcile_pro_rata_and_reject_excess(client, fpo_auth_headers, buyer_auth_headers, db_session):
    crop = _crop(db_session); contributions = []
    for name, amount in (("Member A", "40"), ("Member B", "35"), ("Member C", "25")):
        member = _member(client, fpo_auth_headers, name)
        receipt = _intake(client, fpo_auth_headers, member["id"], crop, amount, "quintal").json()["data"]
        contributions.append((receipt["id"], amount))
    pool = _pool(client, fpo_auth_headers, contributions); lot = _publish(client, fpo_auth_headers, pool)
    accepted = []
    for amount in ("40", "35"):
        offer = _offer(client, buyer_auth_headers, lot, amount)
        result = client.post(f"/api/v1/offers/{offer['id']}/accept", headers=fpo_auth_headers)
        assert result.status_code == 200, result.text
        accepted.append(result.json()["data"]["transaction_id"])
        rows = db_session.query(FPOMemberTradeAllocation).filter(FPOMemberTradeAllocation.pool_id == uuid.UUID(pool["id"])).all()
        sold = sum((row.sold_quantity for row in rows), Decimal("0"))
        assert sold == sum((Decimal(value) for value in ("40", "35")[:len(accepted)]), Decimal("0"))
        assert db_session.query(FPOMemberTradeAllocation).filter(
            FPOMemberTradeAllocation.transaction_id == uuid.UUID(accepted[-1])
        ).count() == 3
        persisted_pool = db_session.get(FPOPool, uuid.UUID(pool["id"]))
        original_contributions = db_session.query(FPOPoolContribution).filter(
            FPOPoolContribution.pool_id == uuid.UUID(pool["id"])
        ).all()
        assert persisted_pool.quantity == Decimal("100.000")
        assert sum((row.quantity for row in original_contributions), Decimal("0")) == Decimal("100.000")
        lot_row = db_session.get(Lot, uuid.UUID(lot["id"]))
        reserved = sum((row.quantity for row in db_session.query(Reservation).filter(
            Reservation.lot_id == lot_row.id, Reservation.status == "ACTIVE"
        ).all()), Decimal("0"))
        assert lot_row.quantity - reserved == Decimal("100.00") - sold
    third = _offer(client, buyer_auth_headers, lot, "30")
    assert client.post(f"/api/v1/offers/{third['id']}/accept", headers=fpo_auth_headers).status_code == 409
    rows = db_session.query(FPOMemberTradeAllocation).filter(FPOMemberTradeAllocation.pool_id == uuid.UUID(pool["id"])).all()
    assert sum((row.sold_quantity for row in rows), Decimal("0")) == Decimal("75.00")
    assert db_session.query(FPOPoolContribution).filter(FPOPoolContribution.pool_id == uuid.UUID(pool["id"])).count() == 3
    assert all(db_session.get(Transaction, uuid.UUID(txn)) for txn in accepted)


def test_proportional_quantity_and_money_rounding_are_separate_and_exact(client, fpo_auth_headers, buyer_auth_headers, db_session):
    crop = _crop(db_session); contributions = []
    for name in ("Member A", "Member B", "Member C"):
        member = _member(client, fpo_auth_headers, name)
        receipt = _intake(client, fpo_auth_headers, member["id"], crop, "1", "quintal").json()["data"]
        contributions.append((receipt["id"], "1"))
    pool = _pool(client, fpo_auth_headers, contributions); lot = _publish(client, fpo_auth_headers, pool, "1.01")
    offer = _offer(client, buyer_auth_headers, lot, "1", "1.01")
    response = client.post(f"/api/v1/offers/{offer['id']}/accept", headers={**fpo_auth_headers, "Idempotency-Key": str(uuid.uuid4())})
    assert response.status_code == 200, response.text
    rows = db_session.query(FPOMemberTradeAllocation).filter_by(transaction_id=uuid.UUID(response.json()["data"]["transaction_id"])).order_by(FPOMemberTradeAllocation.contribution_id).all()
    assert sum((row.sold_quantity for row in rows), Decimal("0")) == Decimal("1.000")
    assert [row.sold_quantity for row in rows] == [Decimal("0.334"), Decimal("0.333"), Decimal("0.333")]
    assert sum((row.gross_allocation for row in rows), Decimal("0")) == Decimal("1.01")
    assert [row.gross_allocation for row in rows] == [Decimal("0.33"), Decimal("0.33"), Decimal("0.35")]


def test_accept_retry_is_idempotent_and_trace_crosses_pool_contribution_receipt_member(client, fpo_auth_headers, buyer_auth_headers, db_session):
    crop = _crop(db_session); contributions = []
    for name, amount in (("Member A", "4"), ("Member B", "7"), ("Member C", "9")):
        member = _member(client, fpo_auth_headers, name)
        receipt = _intake(client, fpo_auth_headers, member["id"], crop, amount, "quintal").json()["data"]
        contributions.append((receipt["id"], amount))
    pool = _pool(client, fpo_auth_headers, contributions); lot = _publish(client, fpo_auth_headers, pool)
    offer = _offer(client, buyer_auth_headers, lot, "10")
    retry_key = str(uuid.uuid4()); headers = {**fpo_auth_headers, "Idempotency-Key": retry_key}
    accepted = client.post(f"/api/v1/offers/{offer['id']}/accept", headers=headers)
    replay = client.post(f"/api/v1/offers/{offer['id']}/accept", headers=headers)
    assert accepted.status_code == replay.status_code == 200
    assert accepted.json()["data"]["transaction_id"] == replay.json()["data"]["transaction_id"]
    transaction_id = accepted.json()["data"]["transaction_id"]
    assert db_session.query(Transaction).filter_by(offer_id=uuid.UUID(offer["id"])).count() == 1
    assert db_session.query(FPOMemberTradeAllocation).filter_by(transaction_id=uuid.UUID(transaction_id)).count() == 3
    trace = client.get(f"/api/v1/fpo/trades/{transaction_id}/trace", headers=fpo_auth_headers)
    data = trace.json()["data"]
    assert data["quantity_qtl"] == "10.000" and data["gross"] == "25000.00"
    assert {row["member_name"] for row in data["allocations"]} == {"Member A", "Member B", "Member C"}
    assert len({row["intake_receipt_id"] for row in data["allocations"]}) == 3
    assert all(row["payout_status"] == "PROJECTED" for row in data["allocations"])


def test_buyer_fpo_counter_acceptance_shares_one_trade_room_and_trace(client, fpo_auth_headers, buyer_auth_headers, db_session):
    crop = _crop(db_session); contributions = []
    for name, amount in (("Member A", "4"), ("Member B", "6")):
        member = _member(client, fpo_auth_headers, name)
        receipt = _intake(client, fpo_auth_headers, member["id"], crop, amount, "quintal").json()["data"]
        contributions.append((receipt["id"], amount))
    pool = _pool(client, fpo_auth_headers, contributions)
    lot = _publish(client, fpo_auth_headers, pool)

    discovery = client.get("/api/v1/requirements/discover/lots", headers=buyer_auth_headers)
    discovered = next(row for row in discovery.json()["data"]["items"] if row["id"] == lot["id"])
    assert discovered["seller_type"] == "FPO" and "member" not in str(discovered).lower()

    original = _offer(client, buyer_auth_headers, lot, "5", "2000")
    visible = client.get("/api/v1/offers", headers=fpo_auth_headers)
    assert any(row["id"] == original["id"] for row in visible.json()["data"]["items"])
    counter = client.post(f"/api/v1/offers/{original['id']}/counter", headers=fpo_auth_headers,
        json={"quantity": "5", "price_per_unit": "2100", "unit": "quintal", "message": "Agreed terms"})
    assert counter.status_code == 200, counter.text
    counter_id = counter.json()["data"]["id"]
    accepted = client.post(f"/api/v1/offers/{counter_id}/accept", headers=buyer_auth_headers)
    assert accepted.status_code == 200, accepted.text
    transaction_id = accepted.json()["data"]["transaction_id"]

    buyer_room = client.get(f"/api/v1/trades/{transaction_id}/room", headers=buyer_auth_headers)
    fpo_room = client.get(f"/api/v1/trades/{transaction_id}/room", headers=fpo_auth_headers)
    assert buyer_room.status_code == fpo_room.status_code == 200
    assert buyer_room.json()["data"]["id"] == fpo_room.json()["data"]["id"] == transaction_id
    assert buyer_room.json()["data"]["terms"]["quantity"] == fpo_room.json()["data"]["terms"]["quantity"]
    trace = client.get(f"/api/v1/fpo/trades/{transaction_id}/trace", headers=fpo_auth_headers)
    assert trace.status_code == 200
    assert trace.json()["data"]["quantity_qtl"] == "5.000"
    assert {row["member_name"] for row in trace.json()["data"]["allocations"]} == {"Member A", "Member B"}


def test_cross_fpo_member_intake_pool_offer_and_trace_access_is_denied(client, fpo_auth_headers, buyer_auth_headers, db_session):
    crop = _crop(db_session); member = _member(client, fpo_auth_headers); intake = _intake(client, fpo_auth_headers, member["id"], crop, "10", "quintal").json()["data"]
    pool = _pool(client, fpo_auth_headers, [(intake["id"], "10")]); lot = _publish(client, fpo_auth_headers, pool)
    offer = _offer(client, buyer_auth_headers, lot, "2")
    second_fpo = _other_fpo(client, db_session)
    assert client.get(f"/api/v1/fpo/members/{member['id']}", headers=second_fpo).status_code == 404
    assert client.patch(f"/api/v1/fpo/members/{member['id']}", headers=second_fpo, json={"farmer_name": "Stolen"}).status_code == 404
    assert client.get(f"/api/v1/fpo/intakes/{intake['id']}/receipt", headers=second_fpo).status_code == 404
    assert client.post(f"/api/v1/fpo/intakes/{intake['id']}/corrections", headers=second_fpo, json={"gross_quantity": "9", "reason": "cross tenant"}).status_code == 404
    assert client.post("/api/v1/fpo/pools", headers=second_fpo, json={"contributions": [{"intake_id": intake["id"], "quantity": "1"}]}).status_code == 404
    assert client.get("/api/v1/fpo/pools", headers=second_fpo).json()["data"] == []
    assert client.post(f"/api/v1/fpo/pools/{pool['id']}/publish", headers=second_fpo, json={"asking_price": "1", "location_text": "Other"}).status_code == 404
    denied = client.post(f"/api/v1/offers/{offer['id']}/accept", headers=second_fpo)
    assert denied.status_code == 403
    accepted = client.post(f"/api/v1/offers/{offer['id']}/accept", headers=fpo_auth_headers).json()["data"]
    assert client.get(f"/api/v1/fpo/trades/{accepted['transaction_id']}/trace", headers=second_fpo).status_code == 404


def test_buyer_fpo_projection_has_group_identity_but_no_member_or_ledger_data(client, fpo_auth_headers, buyer_auth_headers, db_session):
    crop = _crop(db_session); member = _member(client, fpo_auth_headers, "Private member name", phone="9876543210")
    intake = _intake(client, fpo_auth_headers, member["id"], crop, "5", "quintal").json()["data"]
    pool = _pool(client, fpo_auth_headers, [(intake["id"], "5")]); lot = _publish(client, fpo_auth_headers, pool)
    result = client.get("/api/v1/requirements/discover/lots", headers=buyer_auth_headers)
    item = next(row for row in result.json()["data"]["items"] if row["id"] == lot["id"])
    assert item["seller_type"] == "FPO" and item["seller_label"] == "FPO listing"
    assert item["seller_name"]
    for secret in ("Private member name", "9876543210", intake["receipt_id"], "member_id", "contributions", "allocations"):
        assert secret not in str(item)


def test_append_only_correction_records_actor_reason_timestamp_and_original(client, fpo_auth_headers, db_session):
    crop = _crop(db_session); member = _member(client, fpo_auth_headers); intake = _intake(client, fpo_auth_headers, member["id"], crop, "1000", "kg").json()["data"]
    response = client.post(f"/api/v1/fpo/intakes/{intake['id']}/corrections", headers=fpo_auth_headers,
                           json={"gross_quantity": "900", "tare_quantity": "0", "reason": "Scale correction"})
    assert response.status_code == 201, response.text
    corrected = response.json()["data"]
    original = db_session.get(FPOIntake, uuid.UUID(intake["id"]))
    assert original and original.is_voided and original.gross_quantity == Decimal("1000.000")
    assert corrected["correction_of_receipt_id"] == intake["receipt_id"] and corrected["correction_reason"] == "Scale correction"
    assert corrected["correction_actor_id"]
    audit = db_session.query(AuditLog).filter_by(action="fpo.intake.correct", entity_id=intake["id"]).one()
    assert audit.actor_id == str(original.correction_actor_id) and audit.before["gross_quantity"] == "1000.000"
    assert audit.after["reason"] == "Scale correction" and audit.created_at is not None


def test_csv_preview_import_is_scoped_validated_idempotent_and_creates_no_users(client, fpo_auth_headers, db_session):
    crop = _crop(db_session); before = db_session.query(User).count()
    assert "user_id" not in FPOMember.__table__.columns
    csv_data = ("member_code,farmer_name,phone,village,district,primary_crop,grade,land_acres\n"
                "C-01,CSV Member,9876543216,,," + crop.name + ",A,1.25\n"
                "C-02,CSV Duplicate Phone,+91 98765 43216,,," + crop.name + ",A,0\n"
                "C-01,Duplicate Code,,,," + crop.name + ",B,1\n")
    headers = {**fpo_auth_headers, "Content-Type": "text/csv; charset=utf-8"}
    preview = client.post("/api/v1/fpo/members/import/preview", headers=headers, content=csv_data.encode())
    assert preview.status_code == 200, preview.text
    assert preview.json()["data"]["accepted_count"] == 1 and preview.json()["data"]["rejected_count"] == 2
    assert db_session.query(FPOMember).filter_by(member_code="C-01").count() == 0
    import_headers = {**headers, "Idempotency-Key": str(uuid.uuid4())}
    first = client.post("/api/v1/fpo/members/import", headers=import_headers, content=csv_data.encode())
    replay = client.post("/api/v1/fpo/members/import", headers=import_headers, content=csv_data.encode())
    assert first.status_code == 201 and replay.status_code == 201
    assert first.json()["data"]["accepted_count"] == 1
    assert first.json()["data"]["accepted"] == replay.json()["data"]["accepted"]
    imported = db_session.query(FPOMember).filter_by(member_code="C-01").one()
    assert imported.phone == "+919876543216" and imported.district is None
    assert db_session.query(User).count() == before
    differently_cased = csv_data.replace("C-01,CSV Member", "c-01,CSV Another")
    repeated_code = client.post("/api/v1/fpo/members/import/preview", headers=headers, content=differently_cased.encode())
    assert repeated_code.status_code == 200
    assert repeated_code.json()["data"]["accepted_count"] == 0


def test_csv_import_rejects_invalid_encoding_and_oversized_body(client, fpo_auth_headers):
    headers = {**fpo_auth_headers, "Content-Type": "text/csv"}
    assert client.post("/api/v1/fpo/members/import/preview", headers=headers, content=b"\xff\xfe").status_code == 400
    huge = b"x" * (1_048_577)
    assert client.post("/api/v1/fpo/members/import/preview", headers=headers, content=huge).status_code == 413


def test_csv_import_bounds_rows_and_rejects_malformed_invalid_phone_and_controls(client, fpo_auth_headers, db_session):
    crop = _crop(db_session)
    headers = {**fpo_auth_headers, "Content-Type": "text/csv; charset=utf-8"}
    columns = "member_code,farmer_name,phone,village,district,primary_crop,grade,land_acres\n"
    malformed = columns + 'C-1,"unterminated,9876543210,,,,' + crop.name + ",A,1\n"
    assert client.post("/api/v1/fpo/members/import/preview", headers=headers, content=malformed.encode()).status_code == 422
    duplicate_header = columns.replace("member_code,farmer_name", "member_code,member_code")
    assert client.post("/api/v1/fpo/members/import/preview", headers=headers,
                       content=duplicate_header.encode()).status_code == 422
    forged_owner_column = columns.rstrip("\n") + ",fpo_id\nC-0,Other FPO,9876543218,,,,,A,1\n"
    assert client.post("/api/v1/fpo/members/import/preview", headers=headers,
                       content=forged_owner_column.encode()).status_code == 422
    invalid_phone = "C-2,Invalid phone,123,,," + crop.name + ",A,1\n"
    control = "C-3,Control name,9876543217,\x01,," + crop.name + ",A,1\n"
    invalid = client.post("/api/v1/fpo/members/import/preview", headers=headers,
                          content=(columns + invalid_phone + control).encode())
    assert invalid.status_code == 200
    assert invalid.json()["data"]["accepted_count"] == 0 and invalid.json()["data"]["rejected_count"] == 2
    row = "C-{index},Member {index},9876543{suffix:04d},,," + crop.name + ",A,1\n"
    too_many = columns + "".join(row.format(index=index, suffix=index) for index in range(1001))
    assert client.post("/api/v1/fpo/members/import/preview", headers=headers,
                       content=too_many.encode()).status_code == 413
