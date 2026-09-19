"""Add reported-price lineage, idempotency and operational counters.

Revision ID: e47b91c6a2d0
Revises: c4e83d2f1a60
Create Date: 2026-09-17
"""
from __future__ import annotations

import hashlib
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "e47b91c6a2d0"
down_revision: Union[str, Sequence[str], None] = "c4e83d2f1a60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _identity(row) -> str:
    values = (
        str(row["source_id"] or "legacy-unattributed"),
        str(row["crop_id"]),
        str(row["market_id"]),
        str(row["variety_id"] or ""),
        str(row["grade"] or "").strip().casefold(),
        row["price_date"].isoformat() if hasattr(row["price_date"], "isoformat") else str(row["price_date"]),
    )
    return "|".join(values)


def upgrade() -> None:
    with op.batch_alter_table("data_source_registry") as batch:
        batch.add_column(sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("freshness_sla_seconds", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("unit_conventions", sa.JSON(), server_default="{}", nullable=False))
        batch.add_column(sa.Column("known_gaps", sa.JSON(), server_default="[]", nullable=False))
        batch.add_column(sa.Column("last_run_status", sa.Text(), nullable=True))
        batch.add_column(sa.Column("last_run_counts", sa.JSON(), nullable=True))

    with op.batch_alter_table("price_sources") as batch:
        batch.add_column(sa.Column("registry_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key("fk_price_sources_registry", "data_source_registry", ["registry_id"], ["id"])

    with op.batch_alter_table("ingestion_runs") as batch:
        batch.add_column(sa.Column("scope_json", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("records_accepted", sa.Integer(), server_default="0", nullable=False))
        batch.add_column(sa.Column("records_updated", sa.Integer(), server_default="0", nullable=False))
        batch.add_column(sa.Column("records_unchanged", sa.Integer(), server_default="0", nullable=False))
        batch.add_column(sa.Column("records_quarantined", sa.Integer(), server_default="0", nullable=False))
        batch.add_column(sa.Column("unresolved_markets", sa.Integer(), server_default="0", nullable=False))
        batch.add_column(sa.Column("unresolved_crops", sa.Integer(), server_default="0", nullable=False))
        batch.add_column(sa.Column("duration_ms", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("provider_failure", sa.Text(), nullable=True))

    with op.batch_alter_table("crop_varieties") as batch:
        batch.add_column(sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False))
        batch.add_column(sa.Column("is_tradable", sa.Boolean(), server_default=sa.true(), nullable=False))

    with op.batch_alter_table("price_observations") as batch:
        batch.drop_constraint("uq_price_obs", type_="unique")
        batch.add_column(sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("grade", sa.Text(), nullable=True))
        batch.add_column(sa.Column("price_unit", sa.Text(), nullable=True))
        batch.add_column(sa.Column("source_unit", sa.Text(), nullable=True))
        batch.add_column(sa.Column("unit_provenance", sa.Text(), nullable=True))
        batch.add_column(sa.Column("arrival_quantity", sa.Numeric(12, 3), nullable=True))
        batch.add_column(sa.Column("arrival_unit", sa.Text(), nullable=True))
        batch.add_column(sa.Column("observation_key", sa.Text(), nullable=True))

    bind = op.get_bind()
    bind.execute(sa.text(
        "UPDATE price_observations SET fetched_at=retrieved_at "
        "WHERE fetched_at IS NULL AND retrieved_at IS NOT NULL"
    ))
    rows = bind.execute(sa.text(
        "SELECT id,source_id,crop_id,market_id,variety_id,grade,price_date FROM price_observations ORDER BY id"
    )).mappings().all()
    seen: set[str] = set()
    for row in rows:
        identity = _identity(row)
        digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        if digest in seen:
            # Retain legacy duplicate rows without merging or deleting historical observations.
            digest = hashlib.sha256(f"{identity}|legacy-row:{row['id']}".encode("utf-8")).hexdigest()
        seen.add(digest)
        bind.execute(
            sa.text("UPDATE price_observations SET observation_key=:key WHERE id=:id"),
            {"key": digest, "id": row["id"]},
        )

    with op.batch_alter_table("price_observations") as batch:
        batch.alter_column("observation_key", existing_type=sa.Text(), nullable=False)
        batch.create_unique_constraint("uq_price_observation_key", ["observation_key"])

    op.create_index("ix_price_obs_crop_date_market", "price_observations", ["crop_id", "price_date", "market_id"])
    op.create_index("ix_price_obs_source_fetched", "price_observations", ["source_id", "fetched_at"])


def downgrade() -> None:
    bind = op.get_bind()
    duplicate = bind.execute(sa.text(
        "SELECT crop_id,market_id,price_date,source_id,count(*) AS n FROM price_observations "
        "GROUP BY crop_id,market_id,price_date,source_id HAVING count(*) > 1 LIMIT 1"
    )).first()
    if duplicate:
        raise RuntimeError(
            "Cannot safely downgrade price identity: observations now contain legitimate variety/grade dimensions. "
            "Export/reconcile those rows before a manual rollback."
        )

    op.drop_index("ix_price_obs_source_fetched", table_name="price_observations")
    op.drop_index("ix_price_obs_crop_date_market", table_name="price_observations")
    with op.batch_alter_table("price_observations") as batch:
        batch.drop_constraint("uq_price_observation_key", type_="unique")
        for name in (
            "observation_key", "arrival_unit", "arrival_quantity", "unit_provenance", "source_unit",
            "price_unit", "grade", "fetched_at",
        ):
            batch.drop_column(name)
        batch.create_unique_constraint("uq_price_obs", ["crop_id", "market_id", "price_date", "source_id"])

    with op.batch_alter_table("crop_varieties") as batch:
        batch.drop_column("is_tradable")
        batch.drop_column("is_active")
    with op.batch_alter_table("ingestion_runs") as batch:
        for name in (
            "scope_json", "provider_failure", "duration_ms", "unresolved_crops", "unresolved_markets",
            "records_quarantined", "records_unchanged", "records_updated", "records_accepted",
        ):
            batch.drop_column(name)
    with op.batch_alter_table("price_sources") as batch:
        batch.drop_constraint("fk_price_sources_registry", type_="foreignkey")
        batch.drop_column("registry_id")
    with op.batch_alter_table("data_source_registry") as batch:
        for name in (
            "last_run_counts", "last_run_status", "known_gaps", "unit_conventions",
            "freshness_sla_seconds", "last_attempt_at",
        ):
            batch.drop_column(name)
