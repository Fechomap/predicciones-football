"""add_pending_mappings_table

Revision ID: 2cf604e868ef
Revises: 7bf2c480ea77
Create Date: 2025-11-19 16:53:01.916086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2cf604e868ef'
down_revision: Union[str, Sequence[str], None] = '7bf2c480ea77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create pending_mappings table."""
    op.create_table(
        'pending_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_football_id', sa.Integer(), nullable=False),
        sa.Column('team_name', sa.String(length=100), nullable=False),
        sa.Column('suggested_footystats_id', sa.Integer(), nullable=True),
        sa.Column('suggested_footystats_name', sa.String(length=100), nullable=True),
        sa.Column('confidence', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index for faster lookups
    op.create_index('ix_pending_mappings_api_football_id', 'pending_mappings', ['api_football_id'])

    # Create foreign key
    op.create_foreign_key(
        'fk_pending_mappings_league_id',
        'pending_mappings', 'league_id_mapping',
        ['league_id'], ['api_football_id']
    )


def downgrade() -> None:
    """Downgrade schema - Drop pending_mappings table."""
    op.drop_index('ix_pending_mappings_api_football_id', table_name='pending_mappings')
    op.drop_table('pending_mappings')
