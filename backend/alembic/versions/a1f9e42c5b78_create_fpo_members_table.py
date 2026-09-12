"""create_fpo_members_table

Revision ID: a1f9e42c5b78
Revises: 6442a44b1f27
Create Date: 2026-09-12 10:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'a1f9e42c5b78'
down_revision: Union[str, Sequence[str], None] = '6442a44b1f27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'fpo_members',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('fpo_id', sa.UUID(), nullable=False),
        sa.Column('farmer_name', sa.Text(), nullable=False),
        sa.Column('phone', sa.Text(), nullable=True),
        sa.Column('village', sa.Text(), nullable=True),
        sa.Column('district', sa.Text(), nullable=True),
        sa.Column('land_acres', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.0'),
        sa.Column('primary_crop', sa.Text(), nullable=False),
        sa.Column('ready_quantity_qtl', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.0'),
        sa.Column('grade', sa.Text(), nullable=True, server_default='A'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['fpo_id'], ['fpo_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fpo_members_fpo_id', 'fpo_members', ['fpo_id'])


def downgrade() -> None:
    op.drop_index('ix_fpo_members_fpo_id', table_name='fpo_members')
    op.drop_table('fpo_members')
