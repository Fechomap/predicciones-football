"""Add last_verified column to team_id_mapping

Revision ID: 7bf2c480ea77
Revises: ccd8fabacc9f
Create Date: 2025-11-18 20:02:34.680554

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bf2c480ea77'
down_revision: Union[str, Sequence[str], None] = 'ccd8fabacc9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
