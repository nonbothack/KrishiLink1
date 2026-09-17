import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.models import (
    AuditLog,
    Lot,
    Offer,
    OutboxEvent,
    TradeEvent,
    TradeTermSnapshot,
    Transaction,
    User,
)
from app.modules.notifications.service import NotificationService


def gen_trade_public_id(db: Session) -> str:
    return f"KL-TRD-{uuid.uuid4().hex[:10].upper()}"


def _get_transaction(db: Session, identifier: str) -> Transaction:
    try:
        uid = uuid.UUID(identifier)
        txn = db.get(Transaction, uid)
        if txn:
            return txn
    except ValueError:
        pass
    txn = db.query(Transaction).filter(Transaction.public_id == identifier).first()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    return txn


def _ensure_participant_or_admin(txn: Transaction, user: User):
    if user.role.lower() in ("admin", "operator"):
        return
    if str(user.id) not in (str(txn.buyer_id), str(txn.seller_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not a participant in this trade",
        )


def derive_next_action(txn: Transaction, user: User) -> dict:
    st = (txn.status or "").upper()
    uid_str = str(user.id)
    is_buyer = uid_str == str(txn.buyer_id)
    is_seller = uid_str == str(txn.seller_id)
    is_admin_or_op = user.role.lower() in ("admin", "operator")

    if st in ("CREATED", "PAYMENT_PENDING", "OFFER_ACCEPTED"):
        return {
            "action_required": True,
            "responsible_role": "buyer",
            "action_title": "Authorize Sandbox Payment",
            "action_description": "Simulated escrow payment required to confirm agreement and lock transaction value.",
            "action_type": "CONFIRM_PAYMENT",
            "is_current_user_action": is_buyer or is_admin_or_op,
        }
    elif st == "PAYMENT_CONFIRMED":
        return {
            "action_required": True,
            "responsible_role": "seller",
            "action_title": "Prepare Produce for Dispatch",
            "action_description": "Payment confirmed in sandbox. Seller must prepare produce quantity for dispatch.",
            "action_type": "PREPARE_DISPATCH",
            "is_current_user_action": is_seller or is_admin_or_op,
        }
    elif st == "READY_FOR_DISPATCH":
        return {
            "action_required": True,
            "responsible_role": "seller",
            "action_title": "Mark as Dispatched",
            "action_description": "Produce is packed and ready. Mark shipment as dispatched towards destination.",
            "action_type": "DISPATCH",
            "is_current_user_action": is_seller or is_admin_or_op,
        }
    elif st == "IN_TRANSIT":
        return {
            "action_required": True,
            "responsible_role": "buyer",
            "action_title": "Confirm Delivery Arrival",
            "action_description": "Shipment is in transit. Buyer must inspect and confirm delivery arrival at destination.",
            "action_type": "CONFIRM_DELIVERY",
            "is_current_user_action": is_buyer or is_admin_or_op,
        }
    elif st == "DELIVERED":
        return {
            "action_required": True,
            "responsible_role": "buyer",
            "action_title": "Accept Produce & Finalize Settlement",
            "action_description": "Produce delivered. Buyer verifies condition and finalizes trade settlement.",
            "action_type": "FINALIZE_ACCEPTANCE",
            "is_current_user_action": is_buyer or is_admin_or_op,
        }
    elif st == "COMPLETED":
        return {
            "action_required": False,
            "responsible_role": "none",
            "action_title": "Trade Settled",
            "action_description": "This trade is successfully completed and settled. Digital trade summary is available.",
            "action_type": "NONE",
            "is_current_user_action": False,
        }
    elif st == "DISPUTED":
        return {
            "action_required": True,
            "responsible_role": "operator",
            "action_title": "Under Dispute Review",
            "action_description": "A grievance or dispute has been opened for this trade. Operator triage is in progress.",
            "action_type": "DISPUTE_REVIEW",
            "is_current_user_action": is_admin_or_op,
        }
    else:
        return {
            "action_required": False,
            "responsible_role": "none",
            "action_title": "Trade Closed",
            "action_description": f"Trade is currently in {st} status.",
            "action_type": "NONE",
            "is_current_user_action": False,
        }


def get_or_create_term_snapshot(db: Session, txn: Transaction) -> TradeTermSnapshot:
    snap = db.query(TradeTermSnapshot).filter(TradeTermSnapshot.transaction_id == txn.id).first()
    if snap:
        return snap

    lot = db.get(Lot, txn.lot_id)
    offer = db.get(Offer, txn.offer_id) if txn.offer_id else None

    crop_name = lot.crop_name if lot else "Agricultural Commodity"
    grade = lot.grade if lot else "A"
    quantity = float(offer.quantity) if offer else (float(lot.quantity) if lot else 100.0)
    unit = lot.unit if lot else "quintal"
    price_per_unit = float(offer.price_per_unit) if offer else (float(lot.asking_price) if lot and lot.asking_price else 2000.0)
    gross_val = float(txn.gross_value) if txn.gross_value else round(quantity * price_per_unit, 2)
    pickup_loc = lot.location_text if lot else "Seller Farm/Warehouse"

    snap = TradeTermSnapshot(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        lot_id=txn.lot_id,
        buyer_id=txn.buyer_id,
        seller_id=txn.seller_id,
        crop_name=crop_name,
        grade=grade,
        quantity=quantity,
        unit=unit,
        price_per_unit=price_per_unit,
        gross_value=gross_val,
        estimated_net_realization=txn.net_realization or round(gross_val * 0.96, 2),
        delivery_window="Standard 3-5 business days",
        pickup_location=pickup_loc,
        delivery_location="Buyer Primary Delivery Facility",
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


def get_trade_room(db: Session, identifier: str, user: User) -> dict:
    txn = _get_transaction(db, identifier)
    _ensure_participant_or_admin(txn, user)

    # Ensure public_id exists
    if not txn.public_id:
        txn.public_id = gen_trade_public_id(db)
        db.commit()
        db.refresh(txn)

    # Ensure terms snapshot
    snap = get_or_create_term_snapshot(db, txn)

    # Fetch parties
    buyer = db.get(User, txn.buyer_id)
    seller = db.get(User, txn.seller_id)

    # Fetch events timeline
    events = (
        db.query(TradeEvent)
        .filter(TradeEvent.transaction_id == txn.id)
        .order_by(TradeEvent.created_at.asc())
        .all()
    )

    # If no initial event exists, seed it
    if not events:
        init_ev = TradeEvent(
            id=uuid.uuid4(),
            transaction_id=txn.id,
            actor_id=txn.buyer_id,
            actor_role="buyer",
            event_type="DOMAIN_EVENT",
            from_status=None,
            to_status="CREATED",
            title="Trade Agreement Formed",
            description=f"Agreed {snap.quantity} {snap.unit} of {snap.crop_name} (Grade {snap.grade}) at Rs. {snap.price_per_unit:,.2f}/{snap.unit}.",
            created_at=txn.created_at or datetime.now(timezone.utc),
        )
        db.add(init_ev)
        db.commit()
        events = [init_ev]

    next_action = derive_next_action(txn, user)

    gross_val = float(txn.gross_value or snap.gross_value or 0.0)
    transport_est = float(txn.transport_cost or 0.0)
    fee_est = float(txn.fees or round(gross_val * 0.02, 2))
    net_est = float(txn.net_realization or round(gross_val - transport_est - fee_est, 2))

    return {
        "id": txn.id,
        "public_id": txn.public_id,
        "status": txn.status,
        "created_at": txn.created_at,
        "updated_at": txn.updated_at,
        "buyer": {
            "id": buyer.id if buyer else txn.buyer_id,
            "full_name": buyer.full_name if buyer else "Buyer Partner",
            "role": buyer.role if buyer else "buyer",
            "location": buyer.location if buyer else None,
            "district": buyer.district if buyer else None,
        },
        "seller": {
            "id": seller.id if seller else txn.seller_id,
            "full_name": seller.full_name if seller else "Farmer / Producer",
            "role": seller.role if seller else "farmer",
            "location": seller.location if seller else None,
            "district": seller.district if seller else None,
        },
        "terms": {
            "crop_name": snap.crop_name,
            "grade": snap.grade,
            "quantity": float(snap.quantity),
            "unit": snap.unit,
            "price_per_unit": float(snap.price_per_unit),
            "gross_value": float(snap.gross_value),
            "estimated_net_realization": float(snap.estimated_net_realization) if snap.estimated_net_realization else None,
            "delivery_window": snap.delivery_window,
            "pickup_location": snap.pickup_location,
            "delivery_location": snap.delivery_location,
            "created_at": snap.created_at,
        },
        "payment": {
            "status": "CONFIRMED_SANDBOX" if txn.status in ("PAYMENT_CONFIRMED", "PROCESSING", "READY_FOR_DISPATCH", "IN_TRANSIT", "DELIVERED", "COMPLETED") else "PENDING_SANDBOX",
            "gross_value": gross_val,
            "transport_cost": transport_est,
            "platform_fee": fee_est,
            "net_realization": net_est,
            "is_sandbox": True,
            "note": "Simulated / Sandbox payment workflow — real banking escrow integration scheduled in Phase 5.",
        },
        "logistics": {
            "status": txn.status if txn.status in ("READY_FOR_DISPATCH", "IN_TRANSIT", "DELIVERED") else "PENDING_SCHEDULE",
            "origin": snap.pickup_location,
            "destination": snap.delivery_location,
            "carrier_status": "Self-arranged / Pilot carrier unassigned",
            "note": "Logistics dispatch orchestration & carrier tracking scheduled in Phase 6.",
        },
        "quality": {
            "agreed_grade": snap.grade,
            "verification_status": "VISUAL_AGREED",
            "note": f"Visual grade agreed as Grade {snap.grade}. Formal lab assaying and quality certificates scheduled in Phase 7.",
        },
        "next_action": next_action,
        "timeline": [
            {
                "id": ev.id,
                "transaction_id": ev.transaction_id,
                "actor_id": ev.actor_id,
                "actor_role": ev.actor_role,
                "event_type": ev.event_type,
                "from_status": ev.from_status,
                "to_status": ev.to_status,
                "title": ev.title,
                "description": ev.description,
                "created_at": ev.created_at,
            }
            for ev in events
        ],
    }


def execute_trade_transition(
    db: Session,
    identifier: str,
    to_status: str,
    user: User,
    request: Request,
    reason: str | None = None,
) -> dict:
    txn = _get_transaction(db, identifier)
    _ensure_participant_or_admin(txn, user)

    old_status = (txn.status or "").upper()
    target_status = to_status.strip().upper()
    is_buyer = str(user.id) == str(txn.buyer_id)
    is_seller = str(user.id) == str(txn.seller_id)
    is_admin_or_op = user.role.lower() in ("admin", "operator")

    # Allowed transitions and RBAC rules
    valid_transitions = {
        "CREATED": ["PAYMENT_CONFIRMED", "CANCELLED", "DISPUTED"],
        "PAYMENT_PENDING": ["PAYMENT_CONFIRMED", "CANCELLED", "DISPUTED"],
        "PAYMENT_CONFIRMED": ["READY_FOR_DISPATCH", "PROCESSING", "CANCELLED", "DISPUTED"],
        "PROCESSING": ["READY_FOR_DISPATCH", "CANCELLED", "DISPUTED"],
        "READY_FOR_DISPATCH": ["IN_TRANSIT", "CANCELLED", "DISPUTED"],
        "IN_TRANSIT": ["DELIVERED", "DISPUTED"],
        "DELIVERED": ["COMPLETED", "DISPUTED"],
        "DISPUTED": ["COMPLETED", "CANCELLED", "REFUNDED"],
    }

    allowed_targets = valid_transitions.get(old_status, [])
    if target_status not in allowed_targets and not is_admin_or_op:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid state transition from {old_status} to {target_status}. Allowed transitions: {allowed_targets}",
        )

    # Role enforcement
    if target_status == "PAYMENT_CONFIRMED" and not (is_buyer or is_admin_or_op):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the buyer or admin can authorize payment.")
    if target_status in ("READY_FOR_DISPATCH", "IN_TRANSIT") and not (is_seller or is_admin_or_op):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the seller or operator can update dispatch status.")
    if target_status == "COMPLETED" and not (is_buyer or is_admin_or_op):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the buyer or admin can confirm completion/acceptance.")

    txn.status = target_status
    txn.updated_at = datetime.now(timezone.utc)
    db.flush()

    # Create timeline domain event
    ev = TradeEvent(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        actor_id=user.id,
        actor_role=user.role,
        event_type="DOMAIN_EVENT",
        from_status=old_status,
        to_status=target_status,
        title=f"Trade advanced to {target_status}",
        description=reason or f"Action executed by {user.role} ({user.full_name}).",
    )
    db.add(ev)

    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="trade.transition",
            entity="transactions",
            entity_id=str(txn.id),
            before={"status": old_status},
            after={"status": target_status, "reason": reason},
            request_id=rid,
        )
    )
    db.add(
        OutboxEvent(
            aggregate="trades",
            aggregate_id=str(txn.id),
            event_type="trade.status_changed",
            payload={"trade_id": str(txn.id), "from_status": old_status, "to_status": target_status},
        )
    )

    # Notify counterparty
    recipient_id = txn.seller_id if is_buyer else txn.buyer_id
    NotificationService.create_notification(
        db=db,
        user_id=recipient_id,
        type_="trade_update",
        title="Trade Status Updated",
        message=f"Trade #{txn.public_id or str(txn.id)[:8]} status changed from {old_status} to {target_status}.",
        related_id=txn.id,
        outbox=True,
    )

    db.commit()
    return get_trade_room(db, str(txn.id), user)


def add_trade_note(db: Session, identifier: str, user: User, note: str, request: Request) -> TradeEvent:
    txn = _get_transaction(db, identifier)
    _ensure_participant_or_admin(txn, user)

    ev = TradeEvent(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        actor_id=user.id,
        actor_role=user.role,
        event_type="USER_NOTE",
        from_status=txn.status,
        to_status=txn.status,
        title=f"Note from {user.full_name} ({user.role.title()})",
        description=note,
    )
    db.add(ev)
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="trade.note_added",
            entity="transactions",
            entity_id=str(txn.id),
            after={"note_preview": note[:100]},
            request_id=rid,
        )
    )
    db.commit()
    db.refresh(ev)
    return ev
