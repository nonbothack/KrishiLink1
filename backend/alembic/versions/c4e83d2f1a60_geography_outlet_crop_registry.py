"""Add geography references, outlet provenance and canonical crop metadata.

Revision ID: c4e83d2f1a60
Revises: 790546cf29fe
Create Date: 2026-09-17
"""
from __future__ import annotations

import re
import hashlib
import json
import unicodedata
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4e83d2f1a60"
down_revision: Union[str, Sequence[str], None] = "790546cf29fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _slug(value: str, fallback: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug or fallback


def upgrade() -> None:
    op.create_table(
        "geo_states",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lgd_code", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("name_hindi", sa.Text(), nullable=True),
        sa.Column("name_marathi", sa.Text(), nullable=True),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lgd_code", name="uq_geo_states_lgd_code"),
    )
    op.create_table(
        "geo_districts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("state_id", sa.Uuid(), nullable=False),
        sa.Column("lgd_code", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("name_hindi", sa.Text(), nullable=True),
        sa.Column("name_marathi", sa.Text(), nullable=True),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(["state_id"], ["geo_states.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lgd_code", name="uq_geo_districts_lgd_code"),
        sa.UniqueConstraint("state_id", "name", name="uq_geo_district_state_name"),
    )
    op.create_table(
        "geo_subdistricts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("district_id", sa.Uuid(), nullable=False),
        sa.Column("lgd_code", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("name_hindi", sa.Text(), nullable=True),
        sa.Column("name_marathi", sa.Text(), nullable=True),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["geo_districts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lgd_code", name="uq_geo_subdistricts_lgd_code"),
        sa.UniqueConstraint("district_id", "name", name="uq_geo_subdistrict_district_name"),
    )
    op.create_table(
        "data_source_registry",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_key", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("owner", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("license_name", sa.Text(), nullable=True),
        sa.Column("license_url", sa.Text(), nullable=True),
        sa.Column("license_status", sa.Text(), server_default="unknown", nullable=False),
        sa.Column("retrieval_method", sa.Text(), nullable=True),
        sa.Column("schema_version", sa.Text(), nullable=True),
        sa.Column("expected_cadence", sa.Text(), nullable=True),
        sa.Column("geographic_coverage", sa.Text(), nullable=True),
        sa.Column("dedupe_key", sa.Text(), nullable=True),
        sa.Column("parser_version", sa.Text(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quality_score", sa.Numeric(4, 3), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.CheckConstraint("license_status IN ('approved','restricted','unknown','not_applicable')", name="ck_data_source_license_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key", name="uq_data_source_registry_source_key"),
    )

    # Keep preexisting free-text values intact; remove only the incorrect implicit default.
    with op.batch_alter_table("users") as batch:
        batch.alter_column("state", existing_type=sa.Text(), nullable=True, server_default=None)
        batch.add_column(sa.Column("state_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("district_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("subdistrict_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("coordinate_source", sa.Text(), nullable=True))
        batch.add_column(sa.Column("coordinate_confidence", sa.Numeric(3, 2), nullable=True))
        batch.create_foreign_key("fk_users_state_id_geo_states", "geo_states", ["state_id"], ["id"])
        batch.create_foreign_key("fk_users_district_id_geo_districts", "geo_districts", ["district_id"], ["id"])
        batch.create_foreign_key("fk_users_subdistrict_id_geo_subdistricts", "geo_subdistricts", ["subdistrict_id"], ["id"])

    with op.batch_alter_table("markets") as batch:
        batch.alter_column("district", existing_type=sa.Text(), nullable=True)
        batch.alter_column("state", existing_type=sa.Text(), nullable=True, server_default=None)
        batch.add_column(sa.Column("state_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("district_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("subdistrict_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("normalized_name", sa.Text(), nullable=True))
        batch.add_column(sa.Column("outlet_type", sa.Text(), nullable=True))
        batch.add_column(sa.Column("source_registry_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("source_ref", sa.Text(), nullable=True))
        batch.add_column(sa.Column("source_confidence", sa.Numeric(3, 2), nullable=True))
        batch.add_column(sa.Column("coordinate_source", sa.Text(), nullable=True))
        batch.add_column(sa.Column("coordinate_confidence", sa.Numeric(3, 2), nullable=True))
        batch.add_column(sa.Column("verification_status", sa.Text(), server_default="needs_review", nullable=False))
        batch.add_column(sa.Column("verification_method", sa.Text(), nullable=True))
        batch.add_column(sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("verified_by", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("external_identifier", sa.Text(), nullable=True))
        batch.add_column(sa.Column("operating_days", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("metadata_json", sa.JSON(), server_default="{}", nullable=False))
        batch.create_foreign_key("fk_markets_state_id_geo_states", "geo_states", ["state_id"], ["id"])
        batch.create_foreign_key("fk_markets_district_id_geo_districts", "geo_districts", ["district_id"], ["id"])
        batch.create_foreign_key("fk_markets_subdistrict_id_geo_subdistricts", "geo_subdistricts", ["subdistrict_id"], ["id"])
        batch.create_foreign_key("fk_markets_source_registry_id", "data_source_registry", ["source_registry_id"], ["id"])
        batch.create_foreign_key("fk_markets_verified_by_users", "users", ["verified_by"], ["id"])
        batch.create_check_constraint(
            "ck_market_verification_status",
            "verification_status IN ('unverified','needs_review','verified','rejected','inactive')",
        )
        batch.create_check_constraint(
            "ck_market_coordinate_confidence",
            "coordinate_confidence IS NULL OR (coordinate_confidence >= 0 AND coordinate_confidence <= 1)",
        )
        batch.create_check_constraint(
            "ck_market_source_confidence",
            "source_confidence IS NULL OR (source_confidence >= 0 AND source_confidence <= 1)",
        )

    op.create_index("ix_markets_source_ref", "markets", ["source_registry_id", "source_ref"], unique=True)
    op.create_index("ix_markets_normalized_region", "markets", ["normalized_name", "state_id", "district_id"])
    op.create_index("ix_geo_districts_state", "geo_districts", ["state_id", "is_active"])
    op.create_index("ix_geo_subdistricts_district", "geo_subdistricts", ["district_id", "is_active"])

    with op.batch_alter_table("crop_varieties") as batch:
        batch.add_column(sa.Column("name_hindi", sa.Text(), nullable=True))
        batch.add_column(sa.Column("name_marathi", sa.Text(), nullable=True))
        batch.add_column(sa.Column("agmarknet_name", sa.Text(), nullable=True))

    op.create_table(
        "crop_quality_specs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("crop_id", sa.Uuid(), nullable=False),
        sa.Column("variety_id", sa.Uuid(), nullable=True),
        sa.Column("grade", sa.Text(), nullable=False),
        sa.Column("moisture_max_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("foreign_matter_max_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("size_min_mm", sa.Numeric(7, 2), nullable=True),
        sa.Column("size_max_mm", sa.Numeric(7, 2), nullable=True),
        sa.Column("damage_max_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.CheckConstraint("moisture_max_pct IS NULL OR (moisture_max_pct >= 0 AND moisture_max_pct <= 100)", name="ck_quality_moisture_pct"),
        sa.CheckConstraint("damage_max_pct IS NULL OR (damage_max_pct >= 0 AND damage_max_pct <= 100)", name="ck_quality_damage_pct"),
        sa.ForeignKeyConstraint(["crop_id"], ["crops.id"]),
        sa.ForeignKeyConstraint(["variety_id"], ["crop_varieties.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("crop_id", "variety_id", "grade", name="uq_crop_quality_grade"),
    )
    op.create_index("ix_crop_quality_specs_crop_active", "crop_quality_specs", ["crop_id", "is_active"])

    with op.batch_alter_table("crops") as batch:
        batch.add_column(sa.Column("slug", sa.Text(), nullable=True))
        batch.add_column(sa.Column("aliases", sa.JSON(), server_default="[]", nullable=False))
        batch.add_column(sa.Column("valid_units", sa.JSON(), server_default='["quintal"]', nullable=False))
        batch.add_column(sa.Column("agmarknet_name", sa.Text(), nullable=True))
        batch.add_column(sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False))
        batch.add_column(sa.Column("is_tradable", sa.Boolean(), server_default=sa.true(), nullable=False))

    bind = op.get_bind()
    crops = bind.execute(sa.text("SELECT id, name, unit FROM crops ORDER BY id")).mappings().all()
    used: set[str] = set()
    for crop in crops:
        base = _slug(crop["name"], f"crop-{str(crop['id'])[:8]}")
        slug = base
        suffix = 2
        while slug in used:
            slug = f"{base}-{suffix}"
            suffix += 1
        used.add(slug)
        unit = crop["unit"] or "quintal"
        units = ["quintal", "kg", "tonne"]
        if unit not in units:
            bind.execute(sa.text("UPDATE crops SET unit='quintal' WHERE id=:id"), {"id": crop["id"]})
            unit = "quintal"
        bind.execute(
            sa.text("UPDATE crops SET slug=:slug, aliases=:aliases, valid_units=:units, agmarknet_name=:agmarknet WHERE id=:id").bindparams(
                sa.bindparam("aliases", type_=sa.JSON()), sa.bindparam("units", type_=sa.JSON())
            ),
            {"slug": slug, "aliases": [], "units": units, "agmarknet": crop["name"], "id": crop["id"]},
        )
    registry = [
        ("Onion", "कांदा", "प्याज़", "Vegetable", ["Kanda", "Pyaaz", "Pyaz"], "Onion"),
        ("Tomato", "टोमॅटो", "टमाटर", "Vegetable", ["Tamatar"], "Tomato"),
        ("Soybean", "सोयाबीन", "सोयाबीन", "Oilseed", ["Soyabean", "Soya bean"], "Soyabean"),
        ("Cotton", "कापूस", "कपास", "Cash crop", ["Kapas"], "Cotton"),
        ("Wheat", "गहू", "गेहूँ", "Cereal", ["Gehun"], "Wheat"),
        ("Potato", "बटाटा", "आलू", "Vegetable", ["Batata", "Aloo"], "Potato"),
        ("Chilli", "मिरची", "मिर्च", "Spice", ["Mirchi", "Chili"], "Chilli"),
        ("Rice", "तांदूळ", "चावल", "Cereal", ["Tandul", "Chawal"], "Rice"),
        ("Maize", "मका", "मक्का", "Cereal", ["Makka", "Corn"], "Maize"),
    ]
    for name, mr, hi, category, aliases, agmarknet_name in registry:
        existing = bind.execute(sa.text("SELECT id FROM crops WHERE lower(name)=lower(:name) LIMIT 1"), {"name": name}).first()
        if existing:
            bind.execute(
                sa.text("UPDATE crops SET name_marathi=coalesce(name_marathi,:mr), name_hindi=coalesce(name_hindi,:hi), category=coalesce(category,:category), aliases=:aliases, agmarknet_name=coalesce(agmarknet_name,:agmarknet), is_active=true, is_tradable=true WHERE id=:id").bindparams(sa.bindparam("aliases", type_=sa.JSON())),
                {"mr": mr, "hi": hi, "category": category, "aliases": aliases, "agmarknet": agmarknet_name, "id": existing[0]},
            )
        else:
            crop_id = uuid.uuid4()
            bind.execute(
                sa.text("INSERT INTO crops (id,name,slug,name_marathi,name_hindi,aliases,category,unit,valid_units,agmarknet_name,is_active,is_tradable) VALUES (:id,:name,:slug,:mr,:hi,:aliases,:category,'quintal',:units,:agmarknet,true,true)").bindparams(
                    sa.bindparam("aliases", type_=sa.JSON()), sa.bindparam("units", type_=sa.JSON())
                ),
                {"id": crop_id, "name": name, "slug": _slug(name, f"crop-{str(crop_id)[:8]}"), "mr": mr, "hi": hi, "aliases": aliases, "category": category, "units": ["quintal", "kg", "tonne"], "agmarknet": agmarknet_name},
            )
    op.create_index("ix_crops_slug", "crops", ["slug"], unique=True)
    op.create_index("ix_crops_active_tradable", "crops", ["is_active", "is_tradable"])

    # Existing market rows are retained as candidates. Their historical coordinates
    # are not trusted because provenance is absent; no existing coordinate is erased.
    bind.execute(sa.text("UPDATE markets SET normalized_name = lower(trim(name)), outlet_type = coalesce(market_type, 'market_candidate'), verification_status = 'needs_review', coordinate_source = CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 'unknown_legacy' ELSE NULL END, coordinate_confidence = NULL"))

    # Preserve any source trail already present through dated price observations.
    # The legal reuse status remains unknown until an operator verifies the terms.
    price_sources = bind.execute(sa.text(
        "SELECT DISTINCT ps.id, ps.name, ps.url, ps.adapter FROM price_sources ps "
        "JOIN price_observations po ON po.source_id = ps.id ORDER BY ps.id"
    )).mappings().all()
    for source in price_sources:
        source_id = source["id"]
        key = f"legacy-price-source-{source_id}"
        registry_id = bind.execute(sa.text("SELECT id FROM data_source_registry WHERE source_key=:key"), {"key": key}).first()
        if registry_id:
            registry_id = registry_id[0]
        else:
            registry_id = uuid.uuid4()
            bind.execute(sa.text(
                "INSERT INTO data_source_registry (id,source_key,name,owner,url,license_status,retrieval_method,"
                "parser_version,dedupe_key,is_active) VALUES (:id,:key,:name,'Unknown legacy publisher',:url,"
                "'unknown','historical price observation',:parser,'state+district+market label',true)"
            ), {"id": registry_id, "key": key, "name": source["name"], "url": source["url"], "parser": source["adapter"]})
        linked_markets = bind.execute(sa.text(
            "SELECT DISTINCT m.id,m.name,m.district,m.state FROM markets m "
            "JOIN price_observations po ON po.market_id=m.id WHERE po.source_id=:source_id ORDER BY m.id"
        ), {"source_id": source_id}).mappings().all()
        for market in linked_markets:
            assigned = bind.execute(sa.text("SELECT source_registry_id FROM markets WHERE id=:id"), {"id": market["id"]}).first()
            if assigned and assigned[0] is not None:
                continue
            identity = "|".join((str(market["state"] or "").strip().casefold(), str(market["district"] or "").strip().casefold(), str(market["name"]).strip().casefold()))
            source_ref = "legacy-price-label:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()
            bind.execute(sa.text(
                "UPDATE markets SET source_registry_id=:source_id,source_ref=:source_ref "
                "WHERE id=:id AND source_registry_id IS NULL"
            ), {"source_id": registry_id, "source_ref": source_ref, "id": market["id"]})


def downgrade() -> None:
    op.drop_index("ix_crop_quality_specs_crop_active", table_name="crop_quality_specs")
    op.drop_table("crop_quality_specs")
    with op.batch_alter_table("crop_varieties") as batch:
        batch.drop_column("agmarknet_name")
        batch.drop_column("name_marathi")
        batch.drop_column("name_hindi")
    op.drop_index("ix_crops_active_tradable", table_name="crops")
    op.drop_index("ix_crops_slug", table_name="crops")
    with op.batch_alter_table("crops") as batch:
        batch.drop_column("is_tradable")
        batch.drop_column("is_active")
        batch.drop_column("agmarknet_name")
        batch.drop_column("valid_units")
        batch.drop_column("aliases")
        batch.drop_column("slug")

    op.drop_index("ix_geo_subdistricts_district", table_name="geo_subdistricts")
    op.drop_index("ix_geo_districts_state", table_name="geo_districts")
    op.drop_index("ix_markets_normalized_region", table_name="markets")
    op.drop_index("ix_markets_source_ref", table_name="markets")
    with op.batch_alter_table("markets") as batch:
        batch.drop_constraint("ck_market_coordinate_confidence", type_="check")
        batch.drop_constraint("ck_market_source_confidence", type_="check")
        batch.drop_constraint("ck_market_verification_status", type_="check")
        for name in ("verified_by", "source_registry_id", "subdistrict_id", "district_id", "state_id"):
            batch.drop_constraint(f"fk_markets_{name}_geo_{'subdistricts' if name == 'subdistrict_id' else 'districts' if name == 'district_id' else 'states'}", type_="foreignkey") if name in ("subdistrict_id", "district_id", "state_id") else None
        batch.drop_constraint("fk_markets_source_registry_id", type_="foreignkey")
        batch.drop_constraint("fk_markets_verified_by_users", type_="foreignkey")
        for name in ("metadata_json", "operating_days", "external_identifier", "last_reviewed_at", "verified_at", "verified_by", "verification_method", "verification_status", "coordinate_confidence", "coordinate_source", "source_confidence", "source_ref", "source_registry_id", "outlet_type", "normalized_name", "subdistrict_id", "district_id", "state_id"):
            batch.drop_column(name)
        batch.alter_column("district", existing_type=sa.Text(), nullable=False)
        batch.alter_column("state", existing_type=sa.Text(), nullable=True, server_default=None)
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("fk_users_subdistrict_id_geo_subdistricts", type_="foreignkey")
        batch.drop_constraint("fk_users_district_id_geo_districts", type_="foreignkey")
        batch.drop_constraint("fk_users_state_id_geo_states", type_="foreignkey")
        for name in ("coordinate_confidence", "coordinate_source", "subdistrict_id", "district_id", "state_id"):
            batch.drop_column(name)
        batch.alter_column("state", existing_type=sa.Text(), nullable=True, server_default=None)
    op.drop_table("data_source_registry")
    op.drop_table("geo_subdistricts")
    op.drop_table("geo_districts")
    op.drop_table("geo_states")
