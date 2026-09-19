"""Preserve farmer-entered lot units beside canonical quintal quantity.

Revision ID: 73b4c9e10a62
Revises: f5a71b8c2d04
Create Date: 2026-09-17
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "73b4c9e10a62"
down_revision: Union[str, Sequence[str], None] = "f5a71b8c2d04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("lots") as batch:
        batch.add_column(sa.Column("original_quantity", sa.Numeric(12, 3), nullable=True))
        batch.add_column(sa.Column("original_unit", sa.Text(), nullable=True))
        batch.drop_constraint("ck_lot_grade", type_="check")
        batch.create_check_constraint("ck_lot_grade", "grade IN ('A','B','C','UNSPECIFIED')")


def downgrade() -> None:
    connection = op.get_bind()
    unspecified = connection.execute(sa.text("SELECT count(*) FROM lots WHERE grade = 'UNSPECIFIED'")).scalar_one()
    if unspecified:
        raise RuntimeError(f"Refusing to remove UNSPECIFIED grade support while {unspecified} lots use it")
    with op.batch_alter_table("lots") as batch:
        batch.drop_constraint("ck_lot_grade", type_="check")
        batch.create_check_constraint("ck_lot_grade", "grade IN ('A','B','C')")
        batch.drop_column("original_unit")
        batch.drop_column("original_quantity")
