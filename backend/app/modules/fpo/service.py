import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from decimal import ROUND_DOWN, Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    AuditLog,
    Crop,
    FPOIntake,
    FPOMember,
    FPOMemberTradeAllocation,
    FPOPool,
    FPOPoolContribution,
    FPOProfile,
    Lot,
    Offer,
    TradeTermSnapshot,
    Transaction,
    User,
)
from app.modules.auth.identity import canonicalize_indian_mobile
from app.modules.crops.service import resolve_crop
from app.modules.lots.router import _canonical_lot_values, gen_public_id
from app.modules.lots.units import UNIT_TO_QUINTAL

QUANTITY = Decimal("0.001")
LOT_QUANTITY = Decimal("0.01")
MONEY = Decimal("0.01")


def _decimal(value: object) -> Decimal:
    return Decimal(str(value or 0))


def _public(prefix: str) -> str:
    return f"KL-{prefix}-{uuid.uuid4().hex[:10].upper()}"


def _safe_phone(value: str) -> str | None:
    try:
        return canonicalize_indian_mobile(value)[0]
    except ValueError:
        return None


class FPOService:
    @staticmethod
    def get_or_create_fpo_profile(db: Session, user: User) -> FPOProfile:
        profile = db.query(FPOProfile).filter(FPOProfile.user_id == user.id).first()
        if profile is None:
            profile = FPOProfile(id=uuid.uuid4(), user_id=user.id, organization_name=user.full_name,
                registration_number=None, member_count=0, total_land_acres=Decimal("0"), primary_crops=[])
            db.add(profile); db.commit(); db.refresh(profile)
        return profile

    @staticmethod
    def _profile(db: Session, user: User) -> FPOProfile:
        return FPOService.get_or_create_fpo_profile(db, user)

    @staticmethod
    def _intake_available(db: Session, intake: FPOIntake) -> Decimal:
        if intake.is_voided:
            return Decimal("0")
        used = sum((_decimal(row.quantity) for row in db.query(FPOPoolContribution).filter(
            FPOPoolContribution.intake_id == intake.id).all()), Decimal("0"))
        return _decimal(intake.canonical_quantity) - used

    @staticmethod
    def get_summary(db: Session, user: User) -> dict:
        profile = FPOService._profile(db, user)
        pools = db.query(FPOPool).filter(FPOPool.fpo_id == profile.id).all()
        lots = db.query(Lot).filter(Lot.owner_id == user.id, Lot.deleted_at.is_(None)).all()
        offers = db.query(Offer).filter(Offer.lot_id.in_([lot.id for lot in lots])).all() if lots else []
        trades = db.query(Transaction).filter(Transaction.lot_id.in_([lot.id for lot in lots])).all() if lots else []
        return {"organization_name": profile.organization_name,
                "total_members": db.query(FPOMember).filter(FPOMember.fpo_id == profile.id).count(),
                "intakes": db.query(FPOIntake).filter(FPOIntake.fpo_id == profile.id).count(), "pools": len(pools),
                "published_pools": sum(pool.status in ("PUBLISHED", "PARTIALLY_COMMITTED", "COMMITTED") for pool in pools),
                "active_lots": sum((lot.status or "").upper() == "PUBLISHED" for lot in lots),
                "total_volume_qtl": str(sum((_decimal(pool.quantity) for pool in pools), Decimal("0"))),
                "pending_offers": sum((offer.status or "").upper() == "PENDING" for offer in offers), "trades": len(trades)}

    @staticmethod
    def get_members(db: Session, user: User) -> list[dict]:
        profile = FPOService._profile(db, user)
        members = db.query(FPOMember).filter(FPOMember.fpo_id == profile.id).order_by(FPOMember.created_at.desc()).all()
        return [{"id": str(m.id), "farmer_name": m.farmer_name, "phone": m.phone, "village": m.village,
                 "district": m.district, "land_acres": str(_decimal(m.land_acres)), "primary_crop": m.primary_crop,
                 "grade": m.grade or "UNSPECIFIED", "available_quantity_qtl": str(sum((FPOService._intake_available(db, i) for i in db.query(FPOIntake).filter(FPOIntake.member_id == m.id).all()), Decimal("0"))),
                 "created_at": m.created_at.isoformat() if m.created_at else None} for m in members]

    @staticmethod
    def add_member(db: Session, user: User, data) -> dict:
        profile = FPOService._profile(db, user)
        crop = resolve_crop(db, data.primary_crop, include_inactive=False)
        if crop is None:
            raise HTTPException(422, "Crop is not in the active crop registry")
        phone = None
        if data.phone:
            try:
                phone = canonicalize_indian_mobile(data.phone)[0]
            except ValueError as exc:
                raise HTTPException(422, str(exc)) from exc
            if any(old.phone and _safe_phone(old.phone) == phone for old in db.query(FPOMember).filter(FPOMember.fpo_id == profile.id).all()):
                raise HTTPException(409, "Phone is already assigned to an FPO member")
        member = FPOMember(id=uuid.uuid4(), fpo_id=profile.id, farmer_name=data.farmer_name, phone=data.phone,
                           village=data.village, district=data.district, land_acres=data.land_acres,
                           primary_crop=crop.name, ready_quantity_qtl=Decimal("0"), grade=data.grade)
        member.phone = phone
        db.add(member); profile.member_count = (profile.member_count or 0) + 1; db.commit(); db.refresh(member)
        return {"id": str(member.id), "farmer_name": member.farmer_name, "primary_crop": member.primary_crop,
                "grade": member.grade, "district": member.district}

    @staticmethod
    def get_member(db: Session, user: User, member_id: str) -> dict:
        profile = FPOService._profile(db, user)
        try:
            uid = uuid.UUID(member_id)
        except ValueError:
            raise HTTPException(404, "FPO member not found")
        member = db.query(FPOMember).filter(FPOMember.id == uid, FPOMember.fpo_id == profile.id).first()
        if member is None:
            raise HTTPException(404, "FPO member not found")
        return {"id": str(member.id), "member_code": member.member_code, "farmer_name": member.farmer_name,
                "phone": member.phone, "village": member.village, "district": member.district,
                "primary_crop": member.primary_crop, "grade": member.grade}

    @staticmethod
    def update_member(db: Session, user: User, member_id: str, data) -> dict:
        profile = FPOService._profile(db, user)
        try:
            uid = uuid.UUID(member_id)
        except ValueError:
            raise HTTPException(404, "FPO member not found")
        member = db.query(FPOMember).filter(FPOMember.id == uid, FPOMember.fpo_id == profile.id).with_for_update().first()
        if member is None:
            raise HTTPException(404, "FPO member not found")
        values = data.model_dump(exclude_unset=True)
        if "phone" in values and values["phone"]:
            try:
                values["phone"] = canonicalize_indian_mobile(values["phone"])[0]
            except ValueError as exc:
                raise HTTPException(422, str(exc)) from exc
        if "primary_crop" in values:
            crop = resolve_crop(db, values["primary_crop"], include_inactive=False)
            if crop is None:
                raise HTTPException(422, "Crop is not in the active crop registry")
            values["primary_crop"] = crop.name
        for name, value in values.items():
            setattr(member, name, value)
        db.commit(); db.refresh(member)
        return FPOService.get_member(db, user, str(member.id))

    @staticmethod
    def import_members(db: Session, user: User, rows: list[dict], *, preview: bool) -> dict:
        profile = FPOService._profile(db, user)
        accepted: list[dict] = []
        rejected: list[dict] = []
        seen_codes: set[str] = set()
        existing_codes = {
            str(code).casefold()
            for (code,) in db.query(FPOMember.member_code).filter(
                FPOMember.fpo_id == profile.id, FPOMember.member_code.is_not(None)
            ).all()
        }
        seen_phones: set[str] = set()
        for index, row in enumerate(rows, start=2):
            values = {str(key or "").strip(): str(value or "").strip() for key, value in row.items()}
            errors = []
            member_code = values.get("member_code", "")
            farmer_name = values.get("farmer_name", "")
            phone_raw = values.get("phone", "")
            crop_raw = values.get("primary_crop", "")
            grade = (values.get("grade") or "UNSPECIFIED").upper()
            if not member_code or len(member_code) > 80 or re.search(r"[\x00-\x1f\x7f]", member_code):
                errors.append("valid member_code is required")
            elif member_code.casefold() in seen_codes or member_code.casefold() in existing_codes:
                errors.append("duplicate member_code")
            if not farmer_name or len(farmer_name) > 150 or re.search(r"[\x00-\x1f\x7f]", farmer_name):
                errors.append("valid farmer_name is required")
            canonical_phone = None
            if phone_raw:
                try:
                    canonical_phone = canonicalize_indian_mobile(phone_raw)[0]
                except ValueError:
                    errors.append("invalid Indian mobile number")
                if canonical_phone:
                    duplicate_phone = any(
                        old.phone and _safe_phone(old.phone) == canonical_phone
                        for old in db.query(FPOMember).filter(FPOMember.fpo_id == profile.id).all()
                    )
                    if canonical_phone in seen_phones or duplicate_phone:
                        errors.append("duplicate phone in FPO")
            crop = resolve_crop(db, crop_raw, include_inactive=False) if crop_raw else None
            if crop is None:
                errors.append("primary_crop must match an active canonical crop")
            if grade not in {"A", "B", "C", "UNSPECIFIED"}:
                errors.append("grade must be A, B, C, or UNSPECIFIED")
            district = values.get("district") or None
            village = values.get("village") or None
            if any(re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", item or "") for item in (district, village)):
                errors.append("control characters are not allowed")
            try:
                land_acres = Decimal(values.get("land_acres") or "0")
                if land_acres < 0 or land_acres > Decimal("1000000"):
                    errors.append("land_acres is outside the supported range")
            except Exception:
                land_acres = Decimal("0")
                errors.append("land_acres must be a decimal number")
            if errors:
                rejected.append({"row": index, "member_code": member_code or None, "errors": errors})
                continue
            seen_codes.add(member_code.casefold())
            if canonical_phone:
                seen_phones.add(canonical_phone)
            accepted.append({"member_code": member_code, "farmer_name": farmer_name, "phone": canonical_phone,
                             "village": village, "district": district, "primary_crop": crop.name,
                             "land_acres": land_acres, "grade": grade})
        if not preview and accepted:
            for item in accepted:
                db.add(FPOMember(id=uuid.uuid4(), fpo_id=profile.id, farmer_name=item["farmer_name"], phone=item["phone"],
                    village=item["village"], district=item["district"], primary_crop=item["primary_crop"],
                    land_acres=item["land_acres"], grade=item["grade"], member_code=item["member_code"], ready_quantity_qtl=Decimal("0")))
            profile.member_count = (profile.member_count or 0) + len(accepted)
            db.flush()
        return {"preview": preview, "accepted_count": len(accepted), "rejected_count": len(rejected),
                "accepted": [{key: str(value) if isinstance(value, Decimal) else value for key, value in row.items()} for row in accepted],
                "rejected": rejected}

    @staticmethod
    def _intake_projection(db: Session, intake: FPOIntake) -> dict:
        replacement = db.query(FPOIntake).filter(FPOIntake.correction_of_intake_id == intake.id).first()
        return {"id": str(intake.id), "receipt_id": intake.public_id, "member_id": str(intake.member_id), "crop": intake.crop_name,
                "grade": intake.grade, "gross_quantity": str(intake.gross_quantity), "tare_quantity": str(intake.tare_quantity),
                "net_quantity": str(intake.net_quantity), "unit": intake.unit, "canonical_quantity_qtl": str(intake.canonical_quantity),
                "available_quantity_qtl": str(FPOService._intake_available(db, intake)),
                "is_voided": bool(intake.is_voided), "correction_of_intake_id": str(intake.correction_of_intake_id) if intake.correction_of_intake_id else None,
                "correction_of_receipt_id": db.get(FPOIntake, intake.correction_of_intake_id).public_id if intake.correction_of_intake_id and db.get(FPOIntake, intake.correction_of_intake_id) else None,
                "corrected_by_receipt_id": replacement.public_id if replacement else None,
                "correction_reason": intake.correction_reason, "correction_actor_id": str(intake.correction_actor_id) if intake.correction_actor_id else None,
                "settlement_rate": str(intake.settlement_rate) if intake.settlement_rate is not None else None,
                "created_at": intake.created_at.isoformat() if intake.created_at else None}

    @staticmethod
    def create_intake(db: Session, user: User, data) -> dict:
        profile = FPOService._profile(db, user)
        try: member_id = uuid.UUID(data.member_id)
        except ValueError: raise HTTPException(422, "Invalid member ID")
        member = db.query(FPOMember).filter(FPOMember.id == member_id, FPOMember.fpo_id == profile.id).with_for_update().first()
        if member is None: raise HTTPException(404, "FPO member not found")
        try:
            crop = db.get(Crop, uuid.UUID(data.crop))
        except ValueError:
            crop = resolve_crop(db, data.crop, include_inactive=False)
        if crop is not None and (not crop.is_active or not crop.is_tradable):
            crop = None
        if crop is None: raise HTTPException(404, "Crop not found")
        unit = data.unit.strip().lower(); supported = {str(v).lower() for v in (crop.valid_units or [crop.unit or "quintal"])}
        if unit not in UNIT_TO_QUINTAL or unit not in supported: raise HTTPException(422, "Unit is not supported for this crop")
        net = data.gross_quantity - data.tare_quantity
        if data.gross_quantity < data.tare_quantity: raise HTTPException(422, "Tare cannot exceed gross quantity")
        if net <= 0: raise HTTPException(422, "Net intake quantity must be positive")
        canonical = (net * UNIT_TO_QUINTAL[unit]).quantize(QUANTITY)
        if canonical < QUANTITY: raise HTTPException(422, "Intake is below the supported canonical quantity")
        intake = FPOIntake(id=uuid.uuid4(), public_id=_public("INT"), fpo_id=profile.id, member_id=member.id,
            crop_id=crop.id, crop_name=crop.name, grade=data.grade, gross_quantity=data.gross_quantity,
            tare_quantity=data.tare_quantity, net_quantity=net, unit=unit, canonical_quantity=canonical,
            settlement_rate=data.settlement_rate, notes=data.notes)
        db.add(intake); db.flush(); db.refresh(intake)
        return FPOService._intake_projection(db, intake)

    @staticmethod
    def list_intakes(db: Session, user: User) -> list[dict]:
        profile = FPOService._profile(db, user)
        return [FPOService._intake_projection(db, intake) for intake in db.query(FPOIntake).filter(FPOIntake.fpo_id == profile.id).order_by(FPOIntake.created_at.desc()).all()]

    @staticmethod
    def correct_intake(db: Session, user: User, intake_id: str, data) -> dict:
        profile = FPOService._profile(db, user)
        try:
            uid = uuid.UUID(intake_id)
        except ValueError:
            raise HTTPException(404, "Intake receipt not found")
        original = db.query(FPOIntake).filter(FPOIntake.id == uid, FPOIntake.fpo_id == profile.id).with_for_update().first()
        if original is None:
            raise HTTPException(404, "Intake receipt not found")
        if original.is_voided:
            raise HTTPException(409, "This intake receipt has already been corrected")
        if FPOService._intake_available(db, original) != _decimal(original.canonical_quantity):
            raise HTTPException(409, "An intake with pool contributions cannot be corrected")
        net = data.gross_quantity - data.tare_quantity
        if net <= 0:
            raise HTTPException(422, "Net intake quantity must be positive")
        if data.gross_quantity < data.tare_quantity:
            raise HTTPException(422, "Tare cannot exceed gross quantity")
        canonical = (net * UNIT_TO_QUINTAL[original.unit]).quantize(QUANTITY)
        original.is_voided = True
        original.correction_actor_id = user.id
        corrected = FPOIntake(id=uuid.uuid4(), public_id=_public("INT"), fpo_id=profile.id, member_id=original.member_id,
            crop_id=original.crop_id, crop_name=original.crop_name, grade=original.grade, gross_quantity=data.gross_quantity,
            tare_quantity=data.tare_quantity, net_quantity=net, unit=original.unit, canonical_quantity=canonical,
            settlement_rate=original.settlement_rate, notes=original.notes, correction_of_intake_id=original.id,
            correction_reason=data.reason, correction_actor_id=user.id)
        db.add(corrected)
        db.add(AuditLog(actor_id=str(user.id), action="fpo.intake.correct", entity="fpo_intakes", entity_id=str(original.id),
                        before={"receipt_id": original.public_id, "gross_quantity": str(original.gross_quantity), "tare_quantity": str(original.tare_quantity), "net_quantity": str(original.net_quantity), "unit": original.unit},
                        after={"receipt_id": corrected.public_id, "reason": data.reason}, request_id=None))
        db.commit(); db.refresh(corrected)
        return FPOService._intake_projection(db, corrected)

    @staticmethod
    def create_pool(db: Session, user: User, data) -> dict:
        profile = FPOService._profile(db, user); amounts: dict[uuid.UUID, Decimal] = {}
        for item in data.contributions:
            try: intake_id = uuid.UUID(item.intake_id)
            except ValueError: raise HTTPException(422, "Invalid intake ID")
            if intake_id in amounts: raise HTTPException(422, "An intake can appear only once in a pool")
            amounts[intake_id] = item.quantity.quantize(QUANTITY)
        intakes = db.query(FPOIntake).filter(FPOIntake.id.in_(amounts), FPOIntake.fpo_id == profile.id).with_for_update().all()
        if len(intakes) != len(amounts): raise HTTPException(404, "One or more intake receipts were not found")
        if any(intake.is_voided for intake in intakes): raise HTTPException(409, "A corrected intake receipt cannot be pooled")
        if len({i.crop_id for i in intakes}) != 1 or len({i.grade or "UNSPECIFIED" for i in intakes}) != 1: raise HTTPException(422, "A pool must have one crop and grade")
        for intake in intakes:
            if amounts[intake.id] > FPOService._intake_available(db, intake): raise HTTPException(409, "Pool contribution exceeds available intake quantity")
        first, total = intakes[0], sum(amounts.values(), Decimal("0"))
        pool = FPOPool(id=uuid.uuid4(), public_id=_public("POOL"), fpo_id=profile.id, crop_id=first.crop_id,
                       crop_name=first.crop_name, grade=first.grade, quantity=total, status="READY")
        db.add(pool); db.flush()
        for intake in intakes: db.add(FPOPoolContribution(id=uuid.uuid4(), pool_id=pool.id, intake_id=intake.id, member_id=intake.member_id, quantity=amounts[intake.id]))
        db.commit(); db.refresh(pool); return FPOService._pool_projection(db, pool)

    @staticmethod
    def add_pool_contribution(db: Session, user: User, pool_id: str, intake_id: str, quantity: Decimal) -> dict:
        profile = FPOService._profile(db, user)
        try:
            pool_uuid, intake_uuid = uuid.UUID(pool_id), uuid.UUID(intake_id)
        except ValueError as exc:
            raise HTTPException(404, "Pool or receipt not found") from exc
        pool = db.query(FPOPool).filter(FPOPool.id == pool_uuid, FPOPool.fpo_id == profile.id).with_for_update().first()
        if pool is None:
            raise HTTPException(404, "Pool not found")
        if pool.status != "READY":
            raise HTTPException(409, "Published pool composition is immutable")
        intake = db.query(FPOIntake).filter(FPOIntake.id == intake_uuid, FPOIntake.fpo_id == profile.id).with_for_update().first()
        if intake is None:
            raise HTTPException(404, "Intake receipt not found")
        if intake.is_voided or intake.crop_id != pool.crop_id or (intake.grade or "UNSPECIFIED") != (pool.grade or "UNSPECIFIED"):
            raise HTTPException(422, "Receipt crop and grade must match the pool")
        if quantity <= 0 or quantity.quantize(QUANTITY) != quantity or quantity > FPOService._intake_available(db, intake):
            raise HTTPException(409, "Contribution quantity exceeds receipt availability or precision")
        if db.query(FPOPoolContribution.id).filter(FPOPoolContribution.pool_id == pool.id, FPOPoolContribution.intake_id == intake.id).first():
            raise HTTPException(409, "Receipt already contributes to this pool")
        db.add(FPOPoolContribution(id=uuid.uuid4(), pool_id=pool.id, intake_id=intake.id, member_id=intake.member_id, quantity=quantity))
        pool.quantity = _decimal(pool.quantity) + quantity
        db.commit(); db.refresh(pool)
        return FPOService._pool_projection(db, pool)

    @staticmethod
    def remove_pool_contribution(db: Session, user: User, pool_id: str, contribution_id: str) -> dict:
        profile = FPOService._profile(db, user)
        try:
            pool_uuid, contribution_uuid = uuid.UUID(pool_id), uuid.UUID(contribution_id)
        except ValueError as exc:
            raise HTTPException(404, "Pool contribution not found") from exc
        pool = db.query(FPOPool).filter(FPOPool.id == pool_uuid, FPOPool.fpo_id == profile.id).with_for_update().first()
        if pool is None:
            raise HTTPException(404, "Pool not found")
        if pool.status != "READY":
            raise HTTPException(409, "Published pool composition is immutable")
        contribution = db.query(FPOPoolContribution).filter(FPOPoolContribution.id == contribution_uuid, FPOPoolContribution.pool_id == pool.id).with_for_update().first()
        if contribution is None:
            raise HTTPException(404, "Pool contribution not found")
        pool.quantity = _decimal(pool.quantity) - _decimal(contribution.quantity)
        db.delete(contribution); db.commit(); db.refresh(pool)
        return FPOService._pool_projection(db, pool)

    @staticmethod
    def _pool_projection(db: Session, pool: FPOPool) -> dict:
        count = db.query(FPOPoolContribution).filter(FPOPoolContribution.pool_id == pool.id).count()
        return {"id": str(pool.id), "pool_id": pool.public_id, "crop": pool.crop_name, "grade": pool.grade,
                "quantity_qtl": str(pool.quantity), "status": pool.status, "lot_id": str(pool.lot_id) if pool.lot_id else None,
                "contribution_count": count, "created_at": pool.created_at.isoformat() if pool.created_at else None}

    @staticmethod
    def list_pools(db: Session, user: User) -> list[dict]:
        profile = FPOService._profile(db, user)
        return [FPOService._pool_projection(db, pool) for pool in db.query(FPOPool).filter(FPOPool.fpo_id == profile.id).order_by(FPOPool.created_at.desc()).all()]

    @staticmethod
    def get_fpo_lots(db: Session, user: User) -> list[dict]:
        return [{"id": str(lot.id), "public_id": lot.public_id, "crop": lot.crop_name,
                 "quantity": str(lot.quantity), "unit": lot.unit, "grade": lot.grade,
                 "asking_price": str(lot.asking_price) if lot.asking_price is not None else None,
                 "status": lot.status, "location": lot.location_text}
                for lot in db.query(Lot).filter(Lot.owner_id == user.id, Lot.deleted_at.is_(None)).order_by(Lot.created_at.desc()).all()]

    @staticmethod
    def get_fpo_trades(db: Session, user: User) -> list[dict]:
        lots = db.query(Lot.id, Lot.crop_name).filter(Lot.owner_id == user.id).all()
        crop_by_lot = {row.id: row.crop_name for row in lots}
        if not crop_by_lot:
            return []
        trades = db.query(Transaction).filter(Transaction.seller_id == user.id, Transaction.lot_id.in_(crop_by_lot)).order_by(Transaction.created_at.desc()).all()
        return [{"id": str(row.id), "trade_reference": row.public_id, "crop": crop_by_lot.get(row.lot_id),
                 "status": row.status, "gross": str(row.gross_value) if row.gross_value is not None else None,
                 "created_at": row.created_at.isoformat() if row.created_at else None} for row in trades]

    @staticmethod
    def publish_pool(db: Session, user: User, pool_id: str, data) -> dict:
        profile = FPOService._profile(db, user)
        try: uid = uuid.UUID(pool_id)
        except ValueError: raise HTTPException(404, "Pool not found")
        pool = db.query(FPOPool).filter(FPOPool.id == uid, FPOPool.fpo_id == profile.id).with_for_update().first()
        if pool is None: raise HTTPException(404, "Pool not found")
        if pool.status != "READY": raise HTTPException(409, "Only a ready pool can be published")
        contributions = db.query(FPOPoolContribution).filter(FPOPoolContribution.pool_id == pool.id).with_for_update().all()
        total = sum((_decimal(c.quantity) for c in contributions), Decimal("0"))
        if total != _decimal(pool.quantity): raise HTTPException(409, "Pool contribution total does not reconcile")
        if total.quantize(LOT_QUANTITY) != total:
            raise HTTPException(422, "Marketplace lots support quantity steps of 0.01 quintal")
        crop = db.get(Crop, pool.crop_id); canonical, price, _ = _canonical_lot_values(crop, total, "quintal", data.asking_price)
        lot = Lot(id=uuid.uuid4(), public_id=gen_public_id(db), owner_id=user.id, crop_id=pool.crop_id, crop_name=pool.crop_name,
                  grade=pool.grade or "UNSPECIFIED", quantity=canonical, unit="quintal", original_quantity=canonical, original_unit="quintal",
                  asking_price=price, location_text=data.location_text, district=data.district, status="PUBLISHED",
                  created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        db.add(lot); db.flush(); pool.lot_id = lot.id; pool.status = "PUBLISHED"; db.commit(); db.refresh(lot)
        return {"id": str(lot.id), "public_id": lot.public_id, "pool_id": pool.public_id, "quantity_qtl": str(lot.quantity), "status": lot.status}

    @staticmethod
    def allocate_trade(db: Session, lot: Lot, transaction: Transaction, quantity: Decimal, price: Decimal) -> None:
        owner = db.get(User, lot.owner_id)
        if owner is None or owner.role.lower() != "fpo":
            return
        profile = db.query(FPOProfile).filter(FPOProfile.user_id == lot.owner_id).first()
        if profile is None:
            raise HTTPException(409, "FPO lot is missing its intake pool trace")
        pool = db.query(FPOPool).filter(FPOPool.lot_id == lot.id, FPOPool.fpo_id == profile.id).with_for_update().first()
        if pool is None:
            raise HTTPException(409, "FPO lot is missing its intake pool trace")
        contributions = db.query(FPOPoolContribution).filter(FPOPoolContribution.pool_id == pool.id).with_for_update().order_by(FPOPoolContribution.id).all()
        prior: dict[uuid.UUID, Decimal] = {}
        for row in db.query(FPOMemberTradeAllocation).filter(FPOMemberTradeAllocation.pool_id == pool.id).with_for_update().all():
            prior[row.contribution_id] = prior.get(row.contribution_id, Decimal("0")) + _decimal(row.sold_quantity)
        remaining = {c.id: _decimal(c.quantity) - prior.get(c.id, Decimal("0")) for c in contributions}
        available = sum(remaining.values(), Decimal("0"))
        if quantity > available: raise HTTPException(409, "Pool no longer has enough uncommitted quantity")
        allocations: list[tuple[FPOPoolContribution, Decimal]] = []
        quantity_left = quantity
        # Pro-rate to each member's remaining contribution. Round down first,
        # then distribute milli-quintal residuals in stable contribution order.
        for contribution in contributions:
            member_remaining = remaining[contribution.id]
            share = (quantity * member_remaining / available).quantize(QUANTITY, rounding=ROUND_DOWN) if available else Decimal("0")
            if share > member_remaining: share = member_remaining
            allocations.append((contribution, share)); quantity_left -= share
        for index, (contribution, allocated) in enumerate(allocations):
            if quantity_left <= 0: break
            room = remaining[contribution.id] - allocated
            residual = min(room, quantity_left).quantize(QUANTITY, rounding=ROUND_DOWN)
            allocations[index] = (contribution, allocated + residual)
            quantity_left -= residual
        if quantity_left != 0: raise HTTPException(409, "Pool allocation rounding did not reconcile")
        allocations = [(contribution, sold) for contribution, sold in allocations if sold > 0]
        money_left = (quantity * price).quantize(MONEY)
        for index, (contribution, sold) in enumerate(allocations):
            gross = money_left if index == len(allocations) - 1 else (sold * price).quantize(MONEY, rounding=ROUND_DOWN)
            money_left -= gross
            db.add(FPOMemberTradeAllocation(id=uuid.uuid4(), transaction_id=transaction.id, pool_id=pool.id, contribution_id=contribution.id,
                   member_id=contribution.member_id, sold_quantity=sold, gross_allocation=gross, status="PROJECTED"))
        pool.status = "COMMITTED" if available == quantity else "PARTIALLY_COMMITTED"

    @staticmethod
    def trade_trace(db: Session, user: User, transaction_id: str) -> dict:
        try: uid = uuid.UUID(transaction_id)
        except ValueError: raise HTTPException(404, "Trade not found")
        txn = db.get(Transaction, uid)
        if txn is None or txn.seller_id != user.id: raise HTTPException(404, "Trade not found")
        rows = db.query(FPOMemberTradeAllocation).filter(FPOMemberTradeAllocation.transaction_id == uid).all()
        if not rows: raise HTTPException(404, "No FPO trace exists for this trade")
        result = []
        for row in rows:
            contribution = db.get(FPOPoolContribution, row.contribution_id); intake = db.get(FPOIntake, contribution.intake_id) if contribution else None
            member = db.get(FPOMember, row.member_id)
            pool = db.get(FPOPool, row.pool_id)
            result.append({"member_id": str(row.member_id), "member_code": member.member_code if member else None,
                           "member_name": member.farmer_name if member else None, "intake_receipt_id": intake.public_id if intake else None,
                           "pool_id": pool.public_id if pool else str(row.pool_id), "contribution_id": str(row.contribution_id),
                           "sold_quantity_qtl": str(row.sold_quantity), "gross_allocation": str(row.gross_allocation), "payout_status": row.status})
        return {"trade_id": str(txn.id), "trade_reference": txn.public_id, "allocations": result,
                "quantity_qtl": str(sum((_decimal(r.sold_quantity) for r in rows), Decimal("0"))),
                "gross": str(sum((_decimal(r.gross_allocation) for r in rows), Decimal("0")))}

    @staticmethod
    def export_data(db: Session, user: User, *, domain: str = "all") -> dict:
        """Build a bounded, FPO-owner-scoped portability projection.

        The projection deliberately uses public references and operational facts
        only. It does not include credentials, provider payloads, raw evidence,
        unrelated staff notes or records owned by another FPO.
        """
        profile = FPOService._profile(db, user)
        fpo_id = profile.id
        members = db.query(FPOMember).filter(FPOMember.fpo_id == fpo_id).order_by(FPOMember.id).all()
        intakes = db.query(FPOIntake).filter(FPOIntake.fpo_id == fpo_id).order_by(FPOIntake.id).all()
        pools = db.query(FPOPool).filter(FPOPool.fpo_id == fpo_id).order_by(FPOPool.id).all()
        pool_ids = {row.id for row in pools}
        contributions = db.query(FPOPoolContribution).filter(FPOPoolContribution.pool_id.in_(pool_ids)).order_by(FPOPoolContribution.id).all() if pool_ids else []
        lots = db.query(Lot).filter(Lot.owner_id == user.id, Lot.deleted_at.is_(None)).order_by(Lot.id).all()
        trades = db.query(Transaction).filter(Transaction.seller_id == user.id).order_by(Transaction.id).all()
        term_snapshots = {
            row.transaction_id: row
            for row in db.query(TradeTermSnapshot).filter(TradeTermSnapshot.transaction_id.in_({x.id for x in trades})).all()
        } if trades else {}
        allocations = db.query(FPOMemberTradeAllocation).filter(
            FPOMemberTradeAllocation.pool_id.in_(pool_ids)
        ).order_by(FPOMemberTradeAllocation.id).all() if pool_ids else []
        audits = db.query(AuditLog).filter(AuditLog.actor_id == str(user.id)).order_by(AuditLog.id).all()

        def iso(value):
            return value.isoformat() if value else None

        domain_rows = {
            "members": [{"id": str(x.id), "member_code": x.member_code, "farmer_name": x.farmer_name,
                         "phone": x.phone, "village": x.village, "district": x.district,
                         "primary_crop": x.primary_crop, "grade": x.grade, "land_acres": str(x.land_acres) if x.land_acres is not None else None,
                         "created_at": iso(x.created_at)} for x in members],
            "intakes": [{"id": str(x.id), "public_id": x.public_id, "member_id": str(x.member_id),
                         "crop_name": x.crop_name, "grade": x.grade, "gross_quantity": str(x.gross_quantity),
                         "tare_quantity": str(x.tare_quantity), "net_quantity": str(x.net_quantity), "unit": x.unit,
                         "canonical_quantity_qtl": str(x.canonical_quantity), "settlement_rate": str(x.settlement_rate) if x.settlement_rate is not None else None,
                         "is_voided": x.is_voided, "correction_of_intake_id": str(x.correction_of_intake_id) if x.correction_of_intake_id else None,
                         "created_at": iso(x.created_at)} for x in intakes],
            "pools": [{"id": str(x.id), "public_id": x.public_id, "crop_name": x.crop_name, "grade": x.grade,
                       "quantity_qtl": str(x.quantity), "status": x.status, "lot_id": str(x.lot_id) if x.lot_id else None,
                       "created_at": iso(x.created_at)} for x in pools],
            "contributions": [{"id": str(x.id), "pool_id": str(x.pool_id), "intake_id": str(x.intake_id),
                               "member_id": str(x.member_id), "quantity_qtl": str(x.quantity)} for x in contributions],
            "lots": [{"id": str(x.id), "public_id": x.public_id, "crop_name": x.crop_name, "quantity": str(x.quantity),
                      "unit": x.unit, "grade": x.grade, "asking_price": str(x.asking_price) if x.asking_price is not None else None,
                      "status": x.status, "created_at": iso(x.created_at)} for x in lots],
            "trades": [{"id": str(x.id), "public_id": x.public_id, "lot_id": str(x.lot_id) if x.lot_id else None,
                        "quantity": str(term_snapshots[x.id].quantity) if x.id in term_snapshots else None,
                        "unit": term_snapshots[x.id].unit if x.id in term_snapshots else None,
                        "gross_value": str(x.gross_value) if x.gross_value is not None else None,
                        "status": x.status, "created_at": iso(x.created_at)} for x in trades],
            "allocations": [{"id": str(x.id), "transaction_id": str(x.transaction_id), "pool_id": str(x.pool_id),
                             "contribution_id": str(x.contribution_id), "member_id": str(x.member_id),
                             "sold_quantity_qtl": str(x.sold_quantity), "gross_allocation": str(x.gross_allocation),
                             "status": x.status, "created_at": iso(x.created_at)} for x in allocations],
            "audit": [{"id": str(x.id), "action": x.action, "entity": x.entity, "entity_id": x.entity_id,
                       "request_id": x.request_id, "created_at": iso(x.created_at)} for x in audits],
        }
        if domain != "all" and domain not in domain_rows:
            raise HTTPException(422, "Unsupported export domain")
        selected = domain_rows if domain == "all" else {domain: domain_rows[domain]}
        canonical = json.dumps(selected, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        counts = {key: len(value) for key, value in selected.items()}
        return {
            "manifest": {
                "schema_version": "1.0",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "deployment_identity": "krishilink-application",
                "owner_scope": {"fpo_id": str(fpo_id), "account_id": str(user.id)},
                "domains": list(selected),
                "row_counts": counts,
                "sha256": hashlib.sha256(canonical).hexdigest(),
                "secrets_included": False,
            },
            "data": selected if domain == "all" else None,
            "rows": selected[domain] if domain != "all" else [],
        }
