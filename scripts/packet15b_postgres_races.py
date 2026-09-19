"""Focused Packet 15B PostgreSQL application-race rehearsal.

This is intentionally a disposable, PostgreSQL-only harness. It calls the
same service/router functions used by the API with independent SQLAlchemy
sessions and synchronized worker threads. It never points at the development
database; the caller supplies PACKET15B_DATABASE_URL.
"""

from __future__ import annotations

import os
import json
import threading
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from fastapi import HTTPException, Request
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker

from app.models import (
    BuyerProfile,
    BuyerRequirement,
    Crop,
    FPOIntake,
    FPOMember,
    FPOMemberTradeAllocation,
    FPOPool,
    FPOPoolContribution,
    FPOProfile,
    FraudCase,
    IdempotencyKey,
    Lot,
    Notification,
    Offer,
    OutboxEvent,
    Reservation,
    Transaction,
    User,
    WebPushAttempt,
    WebPushDelivery,
    WebPushSubscription,
)
from app.modules.admin.router import CaseDecisionRequest, decide_fraud_case
from app.modules.fpo.service import FPOService
from app.modules.notifications import web_push_provider
from app.modules.notifications.web_push_service import deliver_notification
from app.modules.offers.router import accept_offer, counter_offer, withdraw_offer


URL = os.environ["PACKET15B_DATABASE_URL"]
engine = create_engine(URL, pool_pre_ping=True, pool_size=20, max_overflow=10)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def _user(db: Session, role: str, label: str) -> User:
    row = User(id=uuid.uuid4(), full_name=label, email=f"{label.lower()}-{uuid.uuid4().hex[:8]}@test.invalid", role=role, is_active=True)
    db.add(row)
    if role == "buyer":
        db.flush()
        db.add(BuyerProfile(user_id=row.id, business_name=label, business_type="trader", crops_interested=["Onion"], is_verified=False))
    db.flush()
    return row


def _crop(db: Session) -> Crop:
    row = Crop(id=uuid.uuid4(), name=f"Packet Onion {uuid.uuid4().hex[:6]}", unit="quintal", valid_units=["quintal", "kg"], is_active=True, is_tradable=True)
    db.add(row); db.flush(); return row


def _request(key: str | None = None, path: str = "/api/v1/offers/test/accept") -> Request:
    req = Request({"type": "http", "method": "POST", "path": path, "headers": [(b"host", b"packet15b.test")]})
    req.state.request_id = str(uuid.uuid4())
    if key:
        req.scope["headers"].append((b"idempotency-key", key.encode()))
    return req


def _run_race(fn, count=2):
    barrier = threading.Barrier(count)
    results = []
    lock = threading.Lock()

    def worker(index):
        db = SessionLocal()
        try:
            barrier.wait(timeout=20)
            value = fn(db, index)
            db.commit()
            result = {"ok": True, "value": value}
        except Exception as exc:  # expected loser paths are recorded
            db.rollback()
            if isinstance(exc, HTTPException):
                result = {"ok": False, "status": exc.status_code, "detail": str(exc.detail)}
            else:
                result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        finally:
            db.close()
        with lock:
            results.append(result)

    threads = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(count)]
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=30)
    if any(thread.is_alive() for thread in threads):
        raise RuntimeError("race worker did not finish")
    return results


def _seed_offer(db: Session, quantity="8.00", lot_quantity="10.00", *, requirement=None, owner=None, buyer=None, crop=None, expires=None):
    owner = owner or _user(db, "farmer", "Farmer")
    buyer = buyer or _user(db, "buyer", "Buyer")
    crop = crop or _crop(db)
    lot = Lot(id=uuid.uuid4(), public_id=f"PK15B-{uuid.uuid4().hex[:10]}", owner_id=owner.id, crop_id=crop.id, crop_name=crop.name, grade="A", quantity=Decimal(lot_quantity), unit="quintal", original_quantity=Decimal(lot_quantity), original_unit="quintal", asking_price=Decimal("100.00"), location_text="Nashik", status="PUBLISHED")
    offer = Offer(id=uuid.uuid4(), lot_id=lot.id, buyer_id=buyer.id, owner_id=owner.id, quantity=Decimal(quantity), price_per_unit=Decimal("125.00"), total_value=Decimal(quantity) * Decimal("125.00"), expires_at=expires or datetime.now(timezone.utc) + timedelta(hours=2), status="PENDING", buyer_requirement_id=requirement.id if requirement else None)
    db.add_all([lot, offer]); db.flush(); return owner, buyer, crop, lot, offer


def _accept(db, offer_id, user, key=None):
    return accept_offer(str(offer_id), _request(key, f"/api/v1/offers/{offer_id}/accept"), db, user)


def main():
    # Evidence must never persist database credentials.
    report = {"database": URL.rsplit("@", 1)[-1], "checks": [], "started_at": datetime.now(timezone.utc).isoformat()}
    db = SessionLocal()
    try:
        owner, buyer, crop, lot, offer = _seed_offer(db)
        db.commit()
        outcomes = _run_race(lambda s, i: _accept(s, offer.id, owner, f"lot-race-{i}"))
        db.refresh(lot)
        accepted = db.query(Transaction).filter(Transaction.offer_id == offer.id).count()
        reserved = db.query(func.coalesce(func.sum(Reservation.quantity), 0)).filter(Reservation.lot_id == lot.id, Reservation.status == "ACTIVE").scalar()
        report["checks"].append({"name": "lot_overallocation", "outcomes": outcomes, "transactions": accepted, "reserved": str(reserved), "invariant": Decimal(str(reserved)) <= lot.quantity and accepted == 1})

        req_owner, req_buyer, req_crop = _user(db, "farmer", "ReqFarmer"), _user(db, "buyer", "ReqBuyer"), _crop(db)
        req = BuyerRequirement(id=uuid.uuid4(), buyer_id=req_buyer.id, crop_id=req_crop.id, crop_name=req_crop.name, quantity_max=Decimal("10.00"), canonical_quantity=Decimal("10.00"), committed_quantity=Decimal("0"), status="ACTIVE", is_active=True, allow_partial=True)
        db.add(req); db.flush()
        _, _, _, req_lot, req_offer = _seed_offer(db, "8.00", "30.00", requirement=req, owner=req_owner, buyer=req_buyer, crop=req_crop)
        # A second linked offer intentionally competes for the same requirement.
        req_offer2 = Offer(id=uuid.uuid4(), lot_id=req_lot.id, buyer_id=req_buyer.id, owner_id=req_owner.id, quantity=Decimal("8.00"), price_per_unit=Decimal("126.00"), expires_at=datetime.now(timezone.utc) + timedelta(hours=2), status="PENDING", buyer_requirement_id=req.id)
        db.add(req_offer2); db.commit()
        outcomes = _run_race(lambda s, i: _accept(s, (req_offer.id if i == 0 else req_offer2.id), req_owner, f"req-race-{i}"))
        db.refresh(req)
        report["checks"].append({"name": "requirement_overfill", "outcomes": outcomes, "committed": str(req.committed_quantity), "requested": str(req.canonical_quantity), "invariant": Decimal(str(req.committed_quantity)) <= req.canonical_quantity})

        # Acceptance versus withdrawal and acceptance versus counter use the real routes.
        _, withdraw_buyer, _, _, race_offer = _seed_offer(db, "2.00", "4.00")
        race_owner = db.get(User, race_offer.owner_id)
        db.commit()
        outcomes = _run_race(lambda s, i: _accept(s, race_offer.id, race_owner, f"withdraw-race-{i}") if i == 0 else withdraw_offer(str(race_offer.id), _request(f"withdraw-{i}", f"/api/v1/offers/{race_offer.id}/withdraw"), s, withdraw_buyer))
        db.refresh(race_offer)
        report["checks"].append({"name": "accept_vs_withdraw", "outcomes": outcomes, "final_status": race_offer.status, "invariant": race_offer.status in {"ACCEPTED", "CANCELLED"}})

        _, counter_buyer, _, _, counter_target = _seed_offer(db, "2.00", "4.00")
        counter_owner = db.get(User, counter_target.owner_id)
        db.commit()
        counter_payload = SimpleNamespace(price_per_unit=Decimal("130.00"), quantity=Decimal("2.00"), unit=None, message="counter")
        outcomes = _run_race(lambda s, i: _accept(s, counter_target.id, counter_owner, f"counter-race-{i}") if i == 0 else counter_offer(str(counter_target.id), counter_payload, _request(f"counter-{i}", f"/api/v1/offers/{counter_target.id}/counter"), s, counter_owner))
        db.refresh(counter_target)
        report["checks"].append({"name": "accept_vs_counter", "outcomes": outcomes, "final_status": counter_target.status, "invariant": counter_target.status in {"ACCEPTED", "COUNTERED"}})

        expired_owner, _, _, _, expired_offer = _seed_offer(db, "1.00", "2.00", expires=datetime.now(timezone.utc) - timedelta(minutes=1))
        db.commit()
        outcome = _run_race(lambda s, i: _accept(s, expired_offer.id, expired_owner, f"expired-{i}"), 2)
        report["checks"].append({"name": "expired_offer", "outcomes": outcome, "transactions": db.query(Transaction).filter(Transaction.offer_id == expired_offer.id).count(), "invariant": db.query(Transaction).filter(Transaction.offer_id == expired_offer.id).count() == 0})

        idem_owner, _, _, _, idem_offer = _seed_offer(db, "1.00", "2.00")
        db.commit()
        first = _accept(db, idem_offer.id, idem_owner, "same-idempotency-key")
        db.commit()
        retry = _accept(db, idem_offer.id, idem_owner, "same-idempotency-key")
        db.commit()
        transactions = db.query(Transaction).filter(Transaction.offer_id == idem_offer.id).count()
        keys = db.query(IdempotencyKey).filter(IdempotencyKey.key.like(f"{idem_owner.id}:%same-idempotency-key")).count()
        report["checks"].append({"name": "duplicate_accept_idempotency", "outcomes": [{"ok": True, "value": first}, {"ok": True, "value": retry}], "transactions": transactions, "keys": keys, "invariant": transactions == 1 and keys == 1 and first["data"]["transaction_id"] == retry["data"]["transaction_id"]})

        # FPO intake contribution race: both workers attempt to consume 6 qtl from a 10 qtl receipt.
        fpo_user = _user(db, "fpo", "FPO Owner"); fpo = FPOProfile(id=uuid.uuid4(), user_id=fpo_user.id, organization_name="Packet FPO", member_count=1, primary_crops=["Onion"]); db.add(fpo); db.flush()
        member = FPOMember(id=uuid.uuid4(), fpo_id=fpo.id, farmer_name="Member One", primary_crop=crop.name, member_code=f"M-{uuid.uuid4().hex[:6]}"); db.add(member); db.flush()
        intake = FPOIntake(id=uuid.uuid4(), public_id=f"INT-{uuid.uuid4().hex[:8]}", fpo_id=fpo.id, member_id=member.id, crop_id=crop.id, crop_name=crop.name, grade="A", gross_quantity=Decimal("10.000"), tare_quantity=0, net_quantity=Decimal("10.000"), unit="quintal", canonical_quantity=Decimal("10.000")); db.add(intake); db.commit()
        def make_pool(s, _):
            data = SimpleNamespace(contributions=[SimpleNamespace(intake_id=str(intake.id), quantity=Decimal("6.000"))])
            return FPOService.create_pool(s, fpo_user, data)
        outcomes = _run_race(make_pool)
        pools = db.query(FPOPool).filter(FPOPool.fpo_id == fpo.id).all()
        contributed = db.query(func.coalesce(func.sum(FPOPoolContribution.quantity), 0)).filter(FPOPoolContribution.intake_id == intake.id).scalar()
        report["checks"].append({"name": "fpo_intake_contribution_race", "outcomes": outcomes, "pools": len(pools), "contributed": str(contributed), "invariant": Decimal(str(contributed)) <= Decimal("10.000")})

        # FPO pool sale and allocation rounding: three contributions, a 1.000 qtl sale.
        pool = pools[0]; pool.status = "READY"
        # Replace the first contribution and add two distinct receipts so the
        # proportional allocation has a deterministic rounding remainder.
        first_contrib = db.query(FPOPoolContribution).filter(FPOPoolContribution.pool_id == pool.id).first()
        first_contrib.quantity = Decimal("3.333")
        extra_members, extra_intakes = [], []
        for n in (2, 3):
            extra_member = FPOMember(id=uuid.uuid4(), fpo_id=fpo.id, farmer_name=f"Member {n}", primary_crop=crop.name, member_code=f"M-{uuid.uuid4().hex[:6]}")
            extra_intake = FPOIntake(id=uuid.uuid4(), public_id=f"INT-{uuid.uuid4().hex[:8]}", fpo_id=fpo.id, member_id=extra_member.id, crop_id=crop.id, crop_name=crop.name, grade="A", gross_quantity=Decimal("3.333"), tare_quantity=0, net_quantity=Decimal("3.333"), unit="quintal", canonical_quantity=Decimal("3.333"))
            extra_members.append(extra_member); extra_intakes.append(extra_intake)
        db.add_all(extra_members); db.flush()
        db.add_all(extra_intakes); db.flush()
        db.add_all([FPOPoolContribution(id=uuid.uuid4(), pool_id=pool.id, intake_id=extra_intakes[0].id, member_id=extra_members[0].id, quantity=Decimal("3.333")), FPOPoolContribution(id=uuid.uuid4(), pool_id=pool.id, intake_id=extra_intakes[1].id, member_id=extra_members[1].id, quantity=Decimal("3.333"))])
        pool.quantity = Decimal("9.999")
        fpo_lot = Lot(id=uuid.uuid4(), public_id=f"PK15B-FPO-{uuid.uuid4().hex[:8]}", owner_id=fpo_user.id, crop_id=crop.id, crop_name=crop.name, grade="A", quantity=Decimal("9.99"), unit="quintal", original_quantity=Decimal("9.99"), original_unit="quintal", asking_price=Decimal("100.00"), location_text="Nashik", status="PUBLISHED"); db.add(fpo_lot); db.flush()
        pool.lot_id = fpo_lot.id
        fpo_buyer = _user(db, "buyer", "FPO Buyer")
        fpo_offer = Offer(id=uuid.uuid4(), lot_id=fpo_lot.id, buyer_id=fpo_buyer.id, owner_id=fpo_user.id, quantity=Decimal("1.00"), price_per_unit=Decimal("101.00"), expires_at=datetime.now(timezone.utc) + timedelta(hours=2), status="PENDING"); db.add(fpo_offer); db.commit()
        outcomes = _run_race(lambda s, i: _accept(s, fpo_offer.id, fpo_user, f"fpo-sale-{i}"), 2)
        allocations = db.query(FPOMemberTradeAllocation).filter(FPOMemberTradeAllocation.pool_id == pool.id).all()
        report["checks"].append({"name": "fpo_pool_sale_allocation_rounding", "outcomes": outcomes, "allocated_quantity": str(sum((Decimal(str(a.sold_quantity)) for a in allocations), Decimal("0"))), "allocated_gross": str(sum((Decimal(str(a.gross_allocation)) for a in allocations), Decimal("0"))), "invariant": sum((Decimal(str(a.sold_quantity)) for a in allocations), Decimal("0")) == Decimal("1.000") and sum((Decimal(str(a.gross_allocation)) for a in allocations), Decimal("0")) == Decimal("101.00")})

        # Web Push concurrent delivery: one notification/device pair, one receipt/attempt.
        push_user = _user(db, "farmer", "Push Farmer")
        notification = Notification(id=uuid.uuid4(), user_id=push_user.id, type="trade_created", title="Trade", message="Update")
        subscription = WebPushSubscription(id=uuid.uuid4(), user_id=push_user.id, endpoint="https://push.example.test/packet15b", endpoint_hash=uuid.uuid4().hex, p256dh="p256dh", auth="auth", language="en", is_active=True)
        db.add_all([notification, subscription]); db.commit()
        original_configured = web_push_provider.configured
        web_push_provider.configured = lambda: True
        try:
            outcomes = _run_race(lambda s, i: deliver_notification(s, str(notification.id), sender=lambda _info, _payload: 201), 2)
        finally:
            web_push_provider.configured = original_configured
        deliveries = db.query(WebPushDelivery).filter(WebPushDelivery.notification_id == notification.id).count()
        attempts = db.query(WebPushAttempt).join(WebPushDelivery).filter(WebPushDelivery.notification_id == notification.id).count()
        report["checks"].append({"name": "web_push_deduplicated_delivery", "outcomes": outcomes, "deliveries": deliveries, "attempts": attempts, "invariant": deliveries == 1 and attempts == 1})

        # Fraud review decision race: the row lock makes exactly one terminal decision win.
        reviewer = _user(db, "fraud_reviewer", "Reviewer")
        case = FraudCase(id=uuid.uuid4(), subject_type="USER", subject_id=str(push_user.id), signal_type="PACKET15B", rule_id="race", rule_version=uuid.uuid4().hex, severity="LOW", evidence_refs=[], status="OPEN")
        db.add(case); db.commit()
        def decide(s, i):
            payload = CaseDecisionRequest(status="RESOLVED" if i == 0 else "DISMISSED", decision="reviewed", reason=f"concurrent review {i}")
            return decide_fraud_case(case.id, payload, _request(f"fraud-{i}", f"/api/v1/admin/fraud/cases/{case.id}/decision"), s, reviewer)
        outcomes = _run_race(decide)
        db.refresh(case)
        report["checks"].append({"name": "fraud_case_decision_race", "outcomes": outcomes, "final_status": case.status, "invariant": sum(1 for item in outcomes if item.get("ok")) == 1})

        # Multi-worker outbox claim probe uses PostgreSQL SKIP LOCKED semantics.
        event = OutboxEvent(id=uuid.uuid4(), aggregate="packet15b", aggregate_id=str(uuid.uuid4()), event_type="PACKET15B", payload={}, status="PENDING")
        db.add(event); db.commit()
        from sqlalchemy import select
        def claim(s, _):
            row = s.execute(select(OutboxEvent).where(OutboxEvent.id == event.id, OutboxEvent.status == "PENDING").with_for_update(skip_locked=True)).scalar_one_or_none()
            if not row: return "SKIPPED"
            row.status = "PROCESSING"; return "CLAIMED"
        outcomes = _run_race(claim)
        report["checks"].append({"name": "outbox_multi_worker_claim", "outcomes": outcomes, "invariant": sum(item.get("value") == "CLAIMED" for item in outcomes) == 1})
    finally:
        db.close()
    report["passed"] = all(check.get("invariant") for check in report["checks"])
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(report, indent=2, default=str))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
