import math
import uuid

from sqlalchemy.orm import Session

from app.models import (
    BuyerProfile,
    BuyerRequirement,
    Lot,
    Match,
    MatchRuleSet,
    User,
)

DEFAULT_WEIGHTS = {"crop": 30, "grade": 15, "quantity": 15, "distance": 15, "price": 10, "time": 5, "verification": 10}


def haversine_km(lat1, lng1, lat2, lng2):
    if None in (lat1, lng1, lat2, lng2):
        return 9999
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def get_active_ruleset(db: Session):
    rs = db.query(MatchRuleSet).filter(MatchRuleSet.is_active == True).first()
    if not rs:
        rs = db.query(MatchRuleSet).filter(MatchRuleSet.version == "v1.0").first()
    if not rs:
        # create default
        rs = MatchRuleSet(version="v1.0", weights=DEFAULT_WEIGHTS, is_active=True)
        db.add(rs)
        db.commit()
        db.refresh(rs)
    return rs


def calculate_crop_score(lot_crop: str, buyer_crops: list[str], weights) -> tuple[int, str]:
    if lot_crop in (buyer_crops or []):
        return weights["crop"], f"Crop {lot_crop} matches buyer interest"
    return 0, f"Crop {lot_crop} not in buyer list"


def calculate_grade_score(lot_grade: str, preferred: str | None, weights) -> tuple[int, str]:
    mapping = {"A": 15, "B": 10, "C": 5}
    base = mapping.get(lot_grade, 5)
    if preferred and lot_grade == preferred:
        return weights["grade"], f"Grade {lot_grade} matches preference ({weights['grade']} pts)"
    # scale base to weight
    scaled = int(base * weights["grade"] / 15)
    return scaled, f"Grade {lot_grade} ({scaled} pts)"


def calculate_quantity_score(lot_qty: float, qmin, qmax, weights) -> tuple[int, str]:
    if qmin is None or qmax is None:
        return weights["quantity"] // 2, "No quantity range specified"
    if qmin <= lot_qty <= qmax:
        return weights["quantity"], f"Quantity {lot_qty} within {qmin}-{qmax}"
    if lot_qty < qmin:
        return int(weights["quantity"] * 0.5), f"Quantity {lot_qty} below min {qmin}"
    return int(weights["quantity"] * 0.3), f"Quantity {lot_qty} above max {qmax}"


def calculate_distance_score(lot_lat, lot_lng, buyer_lat, buyer_lng, weights) -> tuple[int, str]:
    if None in (lot_lat, lot_lng, buyer_lat, buyer_lng):
        return 0, "Location unavailable; distance not scored"
    km = haversine_km(lot_lat, lot_lng, buyer_lat, buyer_lng)
    if km <= 20:
        return weights["distance"], f"Nearby {km:.1f}km (<20km)"
    if km <= 100:
        return int(weights["distance"] * 0.66), f"Within 100km ({km:.1f}km)"
    if km <= 300:
        return int(weights["distance"] * 0.33), f"Within 300km ({km:.1f}km)"
    return 0, f"Distant {km:.1f}km"


def calculate_price_score(lot_price, target_price, weights) -> tuple[int, str]:
    if lot_price is None or target_price is None:
        return int(weights["price"] * 0.5), "No price preference"
    diff = abs(float(lot_price) - float(target_price)) / float(target_price)
    if diff <= 0.05:
        return weights["price"], f"Price close to target (diff {diff * 100:.1f}%)"
    if diff <= 0.15:
        return int(weights["price"] * 0.6), f"Price within 15% (diff {diff * 100:.1f}%)"
    return int(weights["price"] * 0.2), f"Price diff {diff * 100:.1f}%"


def calculate_time_score(lot_from, lot_until, req_from, req_until, weights) -> tuple[int, str]:
    if not req_from and not req_until:
        return weights["time"], "No time constraint"
    # overlap check
    lot_start = lot_from
    lot_end = lot_until
    req_start = req_from
    req_end = req_until
    if lot_start and req_end and lot_start > req_end:
        return 0, "Lot available after requirement"
    if lot_end and req_start and lot_end < req_start:
        return 0, "Lot expires before requirement"
    return weights["time"], "Time window compatible"


def calculate_verification_score(is_verified, weights) -> tuple[int, str]:
    if is_verified:
        return weights["verification"], "Buyer verified"
    return 0, "Buyer not verified"


def generate_explanation(lot, buyer, scores, total):
    return {
        "lot_id": str(lot.id),
        "buyer_id": str(buyer.id),
        "scores": scores,
        "total": total,
        "summary": f"Matched {total}/100 — " + ("Excellent" if total >= 75 else "Good" if total >= 50 else "Fair"),
    }


def find_candidates(db: Session, lot_id: str):
    lot = db.get(Lot, lot_id)
    if not lot:
        lot = db.query(Lot).filter(Lot.public_id == lot_id).first()
    if not lot:
        return None, []
    rs = get_active_ruleset(db)
    weights = rs.weights or DEFAULT_WEIGHTS
    crop_name = lot.crop_name
    # find buyers with requirements or profiles (batch loaded to eliminate N+1 queries)
    buyers = db.query(User).filter(User.role == "buyer", User.is_active == True).all()
    if not buyers:
        return lot, []

    buyer_ids = [b.id for b in buyers]
    profiles_by_user = {p.user_id: p for p in db.query(BuyerProfile).filter(BuyerProfile.user_id.in_(buyer_ids)).all()}
    reqs_by_buyer = {
        r.buyer_id: r
        for r in db.query(BuyerRequirement)
        .filter(BuyerRequirement.buyer_id.in_(buyer_ids), BuyerRequirement.is_active == True)
        .all()
    }

    results = []
    for buyer in buyers:
        profile = profiles_by_user.get(buyer.id)
        req = reqs_by_buyer.get(buyer.id)
        # crops
        buyer_crops = profile.crops_interested if profile and profile.crops_interested else []
        # if has requirement, use its crop
        if req and req.crop_name:
            buyer_crops = [req.crop_name]
        crop_score, crop_exp = calculate_crop_score(crop_name, buyer_crops, weights)
        if crop_score == 0:
            continue
        grade_score, grade_exp = calculate_grade_score(
            lot.grade, (req.grade if req else (profile.preferred_grade if profile else None)), weights
        )
        qmin = (
            float(req.quantity_min)
            if req and req.quantity_min
            else (float(profile.min_quantity_quintals) if profile and profile.min_quantity_quintals else None)
        )
        qmax = (
            float(req.quantity_max)
            if req and req.quantity_max
            else (float(profile.max_quantity_quintals) if profile and profile.max_quantity_quintals else None)
        )
        qty_score, qty_exp = calculate_quantity_score(float(lot.quantity), qmin, qmax, weights)
        # distance - get lat/lng from lot and buyer
        lot_lat = lot_lng = None
        if lot.location_geog:
            try:
                from shapely import wkb

                point = wkb.loads(bytes(lot.location_geog.data))
                lot_lng, lot_lat = point.x, point.y
            except (AttributeError, TypeError, ValueError):
                pass
        # buyer coordinates are used only when a persisted point exists
        buyer_lat = buyer_lng = None
        buyer_location = (profile.location_geog if profile else None) or buyer.location_geog
        if buyer_location:
            try:
                from shapely import wkb

                point = wkb.loads(bytes(buyer_location.data))
                buyer_lng, buyer_lat = point.x, point.y
            except (AttributeError, TypeError, ValueError):
                pass
        dist_score, dist_exp = calculate_distance_score(lot_lat, lot_lng, buyer_lat, buyer_lng, weights)
        price_score, price_exp = calculate_price_score(lot.asking_price, (req.target_price if req else None), weights)
        time_score, time_exp = calculate_time_score(
            lot.available_from,
            lot.available_until,
            (req.required_from if req else None),
            (req.required_until if req else None),
            weights,
        )
        ver_score, ver_exp = calculate_verification_score(
            profile.business_verification_status == "VERIFIED" if profile else False,
            weights,
        )
        total = crop_score + grade_score + qty_score + dist_score + price_score + time_score + ver_score
        scores = {
            "crop": crop_score,
            "grade": grade_score,
            "quantity": qty_score,
            "distance": dist_score,
            "price": price_score,
            "time": time_score,
            "verification": ver_score,
        }
        exps = {
            "crop": crop_exp,
            "grade": grade_exp,
            "quantity": qty_exp,
            "distance": dist_exp,
            "price": price_exp,
            "time": time_exp,
            "verification": ver_exp,
        }
        explanation = generate_explanation(lot, buyer, scores, total)
        explanation["details"] = exps
        results.append(
            {
                "buyer": buyer,
                "profile": profile,
                "score": total,
                "component_scores": scores,
                "explanation": explanation,
                "ruleset": rs,
            }
        )
    results.sort(key=lambda x: x["score"], reverse=True)
    return lot, results


def refresh_matches(db: Session, lot_id: str):
    lot, candidates = find_candidates(db, lot_id)
    if not lot:
        return None
    rs = get_active_ruleset(db)
    for c in candidates:
        existing = (
            db.query(Match)
            .filter(Match.lot_id == lot.id, Match.buyer_id == c["buyer"].id, Match.ruleset_version == rs.version)
            .first()
        )
        if existing:
            existing.component_scores = c["component_scores"]
            existing.final_score = c["score"]
            existing.explanation = c["explanation"]
        else:
            db.add(
                Match(
                    id=uuid.uuid4(),
                    lot_id=lot.id,
                    buyer_id=c["buyer"].id,
                    ruleset_id=rs.id,
                    ruleset_version=rs.version,
                    component_scores=c["component_scores"],
                    final_score=c["score"],
                    explanation=c["explanation"],
                )
            )
    db.commit()
    return candidates
