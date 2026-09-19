"""Canonical crop lookup and normalization helpers."""

import re
import unicodedata
import uuid

from sqlalchemy.orm import Session

from app.models import Crop


def normalize_crop_name(value: str) -> str:
    folded = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"[\w]+", folded, flags=re.UNICODE))


def crop_projection(crop: Crop) -> dict:
    return {
        "id": str(crop.id),
        "slug": crop.slug,
        "name": crop.name,
        "name_en": crop.name,
        "name_hindi": crop.name_hindi,
        "name_marathi": crop.name_marathi,
        "aliases": crop.aliases or [],
        "category": crop.category,
        "valid_units": crop.valid_units or [crop.unit or "quintal"],
        "default_unit": crop.unit or "quintal",
        "unit": crop.unit or "quintal",
        "agmarknet_name": crop.agmarknet_name,
        "is_active": bool(crop.is_active),
        "is_tradable": bool(crop.is_tradable),
        "varieties": [
            {
                "id": str(variety.id),
                "name": variety.name,
                "name_hindi": variety.name_hindi,
                "name_marathi": variety.name_marathi,
                "agmarknet_name": variety.agmarknet_name or variety.code,
            }
            for variety in sorted(crop.varieties, key=lambda item: item.name.casefold())
            if variety.is_active and variety.is_tradable
        ],
        "quality_specs": [
            {
                "grade": spec.grade,
                "moisture_max_pct": float(spec.moisture_max_pct) if spec.moisture_max_pct is not None else None,
                "foreign_matter_max_pct": float(spec.foreign_matter_max_pct) if spec.foreign_matter_max_pct is not None else None,
                "size_min_mm": float(spec.size_min_mm) if spec.size_min_mm is not None else None,
                "size_max_mm": float(spec.size_max_mm) if spec.size_max_mm is not None else None,
                "damage_max_pct": float(spec.damage_max_pct) if spec.damage_max_pct is not None else None,
                "description": spec.description,
                "source_ref": spec.source_ref,
            }
            for spec in sorted(crop.quality_specs, key=lambda item: item.grade.casefold())
            if spec.is_active
        ],
    }


def resolve_crop(db: Session, value: str, *, include_inactive: bool = True) -> Crop | None:
    normalized = normalize_crop_name(value)
    if not normalized:
        return None
    # The registry is intentionally small; aliases are compared in Python so the
    # same normalization works for Unicode Hindi/Marathi names on SQLite/Postgres.
    candidates = db.query(Crop).all()
    for crop in candidates:
        if not include_inactive and (not crop.is_active or not crop.is_tradable):
            continue
        names = [crop.name, crop.slug or "", crop.agmarknet_name or "", *(crop.aliases or [])]
        if any(normalize_crop_name(name) == normalized for name in names if name):
            return crop
    return None


def create_unclassified_crop(db: Session, value: str) -> Crop:
    """Preserve a source commodity without publishing it as selectable/tradable."""
    existing = resolve_crop(db, value)
    if existing:
        return existing
    name = " ".join(value.strip().split())
    if not name:
        raise ValueError("Crop name is required")
    slug = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()).strip("-")
    if not slug:
        slug = f"unclassified-{uuid.uuid4().hex[:12]}"
    base, suffix = slug, 2
    while db.query(Crop.id).filter(Crop.slug == slug).first():
        slug = f"{base}-{suffix}"
        suffix += 1
    crop = Crop(
        id=uuid.uuid4(),
        name=name,
        slug=slug,
        category="unclassified",
        unit="quintal",
        valid_units=["quintal", "kg", "tonne"],
        agmarknet_name=name,
        is_active=False,
        is_tradable=False,
    )
    db.add(crop)
    db.flush()
    return crop
