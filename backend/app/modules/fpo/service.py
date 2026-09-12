import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import Crop, FPOProfile, FPOMember, Lot, Offer, Transaction, User
from app.modules.fpo.schemas import FPOAggregateLotRequest, FPOMemberCreateRequest
from app.modules.lots.router import gen_public_id

logger = logging.getLogger(__name__)

# Sample verified members automatically provisioned for fresh/seeded FPOs
SEED_FPO_MEMBERS = [
    {"farmer_name": "Ramesh Patil", "phone": "9820019061", "village": "Lasalgaon", "district": "Nashik", "land_acres": 4.5, "primary_crop": "Onion", "ready_quantity_qtl": 200, "grade": "A"},
    {"farmer_name": "Sunita Deshpande", "phone": "9820019062", "village": "Deola", "district": "Nashik", "land_acres": 6.0, "primary_crop": "Onion", "ready_quantity_qtl": 300, "grade": "A"},
    {"farmer_name": "Ganesh Shinde", "phone": "9820019063", "village": "Sinnar", "district": "Nashik", "land_acres": 8.0, "primary_crop": "Onion", "ready_quantity_qtl": 500, "grade": "B"},
    {"farmer_name": "Laxmi Jadhav", "phone": "9820019064", "village": "Dindori", "district": "Nashik", "land_acres": 3.5, "primary_crop": "Tomato", "ready_quantity_qtl": 200, "grade": "A"},
    {"farmer_name": "Balu Gholap", "phone": "9820019065", "village": "Yeola", "district": "Nashik", "land_acres": 5.0, "primary_crop": "Soybean", "ready_quantity_qtl": 150, "grade": "A"},
    {"farmer_name": "Shrikant Kadam", "phone": "9820019066", "village": "Niphad", "district": "Nashik", "land_acres": 7.0, "primary_crop": "Wheat", "ready_quantity_qtl": 350, "grade": "A"},
]


class FPOService:
    @staticmethod
    def get_or_create_fpo_profile(db: Session, user: User) -> FPOProfile:
        profile = db.query(FPOProfile).filter(FPOProfile.user_id == user.id).first()
        if not profile:
            profile = FPOProfile(
                id=uuid.uuid4(),
                user_id=user.id,
                organization_name=user.full_name or "Nashik Farmer Collective FPO",
                registration_number=f"MH-FPO-{str(user.id)[:8].upper()}",
                member_count=120,
                total_land_acres=450.0,
                primary_crops=["Onion", "Tomato", "Soybean", "Wheat"],
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)

        # Ensure seed members exist if table is empty for this FPO
        member_count = db.query(FPOMember).filter(FPOMember.fpo_id == profile.id).count()
        if member_count == 0:
            for m in SEED_FPO_MEMBERS:
                db.add(FPOMember(
                    id=uuid.uuid4(),
                    fpo_id=profile.id,
                    farmer_name=m["farmer_name"],
                    phone=m["phone"],
                    village=m["village"],
                    district=m["district"],
                    land_acres=m["land_acres"],
                    primary_crop=m["primary_crop"],
                    ready_quantity_qtl=m["ready_quantity_qtl"],
                    grade=m["grade"],
                ))
            db.commit()

        return profile

    @staticmethod
    def get_summary(db: Session, user: User) -> dict:
        profile = FPOService.get_or_create_fpo_profile(db, user)

        # 1. Total Members
        actual_members = db.query(FPOMember).filter(FPOMember.fpo_id == profile.id).count()
        total_members = max(actual_members, profile.member_count or 0)

        # 2. Lots published by this FPO user
        lots = db.query(Lot).filter(Lot.owner_id == user.id, Lot.deleted_at.is_(None)).all()
        active_lots = [l for l in lots if (l.status or "").upper() in ("PUBLISHED", "ACTIVE", "PARTIALLY_ALLOCATED")]
        total_volume_qtl = sum(float(l.quantity) for l in active_lots)

        # 3. Offers on FPO lots
        lot_ids = [l.id for l in lots]
        offers = (
            db.query(Offer).filter(Offer.lot_id.in_(lot_ids)).all()
            if lot_ids
            else []
        )
        pending_offers = [o for o in offers if (o.status or "").upper() == "PENDING"]
        pending_offers_value = sum(float(o.offered_price) * float(o.quantity) for o in pending_offers)

        # 4. Completed deals / transactions
        txns = (
            db.query(Transaction).filter(Transaction.lot_id.in_(lot_ids)).all()
            if lot_ids
            else []
        )
        completed_txns = [t for t in txns if (t.status or "").upper() in ("COMPLETED", "SETTLED", "DELIVERED")]
        total_revenue = sum(float(t.amount or 0) for t in completed_txns)

        return {
            "organization_name": profile.organization_name,
            "registration_number": profile.registration_number,
            "total_members": total_members,
            "active_lots": len(active_lots),
            "total_volume_qtl": round(total_volume_qtl, 1),
            "pending_offers": len(pending_offers),
            "pending_offers_value": round(pending_offers_value, 2),
            "completed_deals": len(completed_txns),
            "total_revenue": round(total_revenue, 2),
        }

    @staticmethod
    def get_members(db: Session, user: User) -> list[dict]:
        profile = FPOService.get_or_create_fpo_profile(db, user)
        members = (
            db.query(FPOMember)
            .filter(FPOMember.fpo_id == profile.id)
            .order_by(FPOMember.created_at.desc())
            .all()
        )
        return [
            {
                "id": str(m.id),
                "farmer_name": m.farmer_name,
                "phone": m.phone,
                "village": m.village,
                "district": m.district,
                "land_acres": float(m.land_acres or 0.0),
                "primary_crop": m.primary_crop,
                "ready_quantity_qtl": float(m.ready_quantity_qtl or 0.0),
                "grade": m.grade or "A",
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in members
        ]

    @staticmethod
    def add_member(db: Session, user: User, data: FPOMemberCreateRequest) -> dict:
        profile = FPOService.get_or_create_fpo_profile(db, user)
        member = FPOMember(
            id=uuid.uuid4(),
            fpo_id=profile.id,
            farmer_name=data.farmer_name,
            phone=data.phone,
            village=data.village,
            district=data.district or user.district,
            land_acres=data.land_acres,
            primary_crop=data.primary_crop,
            ready_quantity_qtl=data.ready_quantity_qtl,
            grade=data.grade,
        )
        db.add(member)
        # Update FPOProfile member count
        profile.member_count = (profile.member_count or 0) + 1
        db.commit()
        db.refresh(member)
        return {
            "id": str(member.id),
            "farmer_name": member.farmer_name,
            "phone": member.phone,
            "village": member.village,
            "district": member.district,
            "land_acres": float(member.land_acres or 0.0),
            "primary_crop": member.primary_crop,
            "ready_quantity_qtl": float(member.ready_quantity_qtl or 0.0),
            "grade": member.grade,
            "created_at": member.created_at.isoformat() if member.created_at else None,
        }

    @staticmethod
    def get_fpo_lots(db: Session, user: User) -> list[dict]:
        lots = (
            db.query(Lot)
            .filter(Lot.owner_id == user.id, Lot.deleted_at.is_(None))
            .order_by(Lot.created_at.desc())
            .all()
        )
        lot_ids = [l.id for l in lots]
        offers = (
            db.query(Offer).filter(Offer.lot_id.in_(lot_ids)).all()
            if lot_ids
            else []
        )
        offers_by_lot: dict[str, list] = {}
        for o in offers:
            lid = str(o.lot_id)
            if lid not in offers_by_lot:
                offers_by_lot[lid] = []
            offers_by_lot[lid].append({
                "id": str(o.id),
                "buyer_id": str(o.owner_id),
                "offered_price": float(o.offered_price),
                "quantity": float(o.quantity),
                "status": o.status,
                "notes": o.notes,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            })

        results = []
        for l in lots:
            lid = str(l.id)
            results.append({
                "id": lid,
                "public_id": l.public_id,
                "crop": l.crop_name,
                "quantity": float(l.quantity),
                "unit": l.unit or "quintal",
                "grade": l.grade,
                "asking_price": float(l.asking_price) if l.asking_price else None,
                "status": l.status,
                "location": l.location_text,
                "district": l.district,
                "created_at": l.created_at.isoformat() if l.created_at else None,
                "offers_count": len(offers_by_lot.get(lid, [])),
                "offers": offers_by_lot.get(lid, []),
            })
        return results

    @staticmethod
    def aggregate_and_create_lot(db: Session, user: User, data: FPOAggregateLotRequest) -> dict:
        crop = db.query(Crop).filter(Crop.name.ilike(data.crop)).first()
        now_utc = datetime.now(timezone.utc)
        
        # Build notes with provenance
        notes = data.notes or ""
        if data.member_ids:
            members = db.query(FPOMember).filter(FPOMember.id.in_([uuid.UUID(mid) for mid in data.member_ids if mid])).all()
            member_names = [m.farmer_name for m in members]
            if member_names:
                notes = f"Aggregated collective lot from {len(member_names)} members: {', '.join(member_names)}. {notes}".strip()

        lot = Lot(
            id=uuid.uuid4(),
            public_id=gen_public_id(db),
            owner_id=user.id,
            crop_id=crop.id if crop else None,
            crop_name=crop.name if crop else data.crop.capitalize(),
            grade=data.grade or "A",
            quantity=data.quantity,
            unit=data.unit or "quintal",
            asking_price=data.asking_price,
            location_text=data.location_text,
            district=data.district or user.district or "Nashik",
            status="PUBLISHED",
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add(lot)
        db.commit()
        db.refresh(lot)

        return {
            "id": str(lot.id),
            "public_id": lot.public_id,
            "crop": lot.crop_name,
            "quantity": float(lot.quantity),
            "unit": lot.unit,
            "grade": lot.grade,
            "asking_price": float(lot.asking_price),
            "location_text": lot.location_text,
            "district": lot.district,
            "status": lot.status,
            "notes": notes,
            "created_at": lot.created_at.isoformat() if lot.created_at else None,
        }
