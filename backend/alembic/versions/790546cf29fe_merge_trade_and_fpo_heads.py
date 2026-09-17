"""merge trade and fpo heads

Revision ID: 790546cf29fe
Revises: 7a8b9c0d1e2f, a1f9e42c5b78
Create Date: 2026-09-17 10:26:07.028284

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '790546cf29fe'
down_revision: Union[str, Sequence[str], None] = ('7a8b9c0d1e2f', 'a1f9e42c5b78')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
