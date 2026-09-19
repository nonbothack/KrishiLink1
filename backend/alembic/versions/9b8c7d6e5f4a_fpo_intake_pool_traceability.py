"""Add immutable FPO intake, pool contribution and trade allocation records.

Revision ID: 9b8c7d6e5f4a
Revises: 8a7d6e5f4c3b
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "9b8c7d6e5f4a"
down_revision = "8a7d6e5f4c3b"
branch_labels = None
depends_on = None

def upgrade():
    uid = postgresql.UUID(as_uuid=True)
    op.add_column("fpo_members", sa.Column("member_code", sa.Text(), nullable=True))
    op.create_unique_constraint("uq_fpo_member_code", "fpo_members", ["fpo_id", "member_code"])
    op.create_table("fpo_intakes", sa.Column("id", uid, primary_key=True), sa.Column("public_id", sa.Text(), nullable=False, unique=True), sa.Column("fpo_id", uid, sa.ForeignKey("fpo_profiles.id"), nullable=False), sa.Column("member_id", uid, sa.ForeignKey("fpo_members.id"), nullable=False), sa.Column("crop_id", uid, sa.ForeignKey("crops.id"), nullable=False), sa.Column("crop_name", sa.Text(), nullable=False), sa.Column("grade", sa.Text()), sa.Column("gross_quantity", sa.Numeric(12,3), nullable=False), sa.Column("tare_quantity", sa.Numeric(12,3), nullable=False, server_default="0"), sa.Column("net_quantity", sa.Numeric(12,3), nullable=False), sa.Column("unit", sa.Text(), nullable=False), sa.Column("canonical_quantity", sa.Numeric(12,3), nullable=False), sa.Column("settlement_rate", sa.Numeric(12,2)), sa.Column("notes", sa.Text()), sa.Column("correction_of_intake_id", uid, sa.ForeignKey("fpo_intakes.id")), sa.Column("correction_reason", sa.Text()), sa.Column("correction_actor_id", uid, sa.ForeignKey("users.id")), sa.Column("is_voided", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_table("fpo_pools", sa.Column("id", uid, primary_key=True), sa.Column("public_id", sa.Text(), nullable=False, unique=True), sa.Column("fpo_id", uid, sa.ForeignKey("fpo_profiles.id"), nullable=False), sa.Column("crop_id", uid, sa.ForeignKey("crops.id"), nullable=False), sa.Column("crop_name", sa.Text(), nullable=False), sa.Column("grade", sa.Text()), sa.Column("quantity", sa.Numeric(12,3), nullable=False), sa.Column("status", sa.Text(), nullable=False, server_default="READY"), sa.Column("lot_id", uid, sa.ForeignKey("lots.id"), unique=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_table("fpo_pool_contributions", sa.Column("id", uid, primary_key=True), sa.Column("pool_id", uid, sa.ForeignKey("fpo_pools.id"), nullable=False), sa.Column("intake_id", uid, sa.ForeignKey("fpo_intakes.id"), nullable=False), sa.Column("member_id", uid, sa.ForeignKey("fpo_members.id"), nullable=False), sa.Column("quantity", sa.Numeric(12,3), nullable=False), sa.UniqueConstraint("pool_id", "intake_id", name="uq_fpo_pool_intake_contribution"))
    op.create_table("fpo_member_trade_allocations", sa.Column("id", uid, primary_key=True), sa.Column("transaction_id", uid, sa.ForeignKey("transactions.id"), nullable=False), sa.Column("pool_id", uid, sa.ForeignKey("fpo_pools.id"), nullable=False), sa.Column("contribution_id", uid, sa.ForeignKey("fpo_pool_contributions.id"), nullable=False), sa.Column("member_id", uid, sa.ForeignKey("fpo_members.id"), nullable=False), sa.Column("sold_quantity", sa.Numeric(12,3), nullable=False), sa.Column("gross_allocation", sa.Numeric(12,2), nullable=False), sa.Column("status", sa.Text(), nullable=False, server_default="PROJECTED"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.UniqueConstraint("transaction_id", "contribution_id", name="uq_fpo_trade_contribution"))
def downgrade():
    op.drop_table("fpo_member_trade_allocations"); op.drop_table("fpo_pool_contributions"); op.drop_table("fpo_pools"); op.drop_table("fpo_intakes")
    op.drop_constraint("uq_fpo_member_code", "fpo_members", type_="unique")
    op.drop_column("fpo_members", "member_code")
