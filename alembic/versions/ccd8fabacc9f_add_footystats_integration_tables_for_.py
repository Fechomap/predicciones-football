"""Add FootyStats integration tables for Railway

Revision ID: ccd8fabacc9f
Revises: 613908a56b23
Create Date: 2025-11-18 19:58:50.174199

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ccd8fabacc9f'
down_revision: Union[str, Sequence[str], None] = '613908a56b23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add FootyStats integration tables."""

    # Create league_id_mapping table
    op.create_table(
        'league_id_mapping',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('api_football_id', sa.Integer(), nullable=False),
        sa.Column('footystats_id', sa.Integer(), nullable=False),
        sa.Column('league_name', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=50), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_football_id')
    )
    op.create_index('idx_league_api_id', 'league_id_mapping', ['api_football_id'])

    # Create team_id_mapping table
    op.create_table(
        'team_id_mapping',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('api_football_id', sa.Integer(), nullable=False),
        sa.Column('footystats_id', sa.Integer(), nullable=True),
        sa.Column('team_name', sa.String(length=100), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('last_verified', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['league_id'], ['league_id_mapping.api_football_id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_football_id')
    )
    op.create_index('idx_team_api_id', 'team_id_mapping', ['api_football_id'])
    op.create_index('idx_team_footystats_id', 'team_id_mapping', ['footystats_id'])

    # Create analysis_history table
    op.create_table(
        'analysis_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fixture_id', sa.Integer(), nullable=False),
        sa.Column('pdf_url', sa.Text(), nullable=True),
        sa.Column('pdf_cloudflare_key', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('analysis_type', sa.String(length=50), nullable=True),
        sa.Column('home_team_name', sa.String(length=100), nullable=True),
        sa.Column('away_team_name', sa.String(length=100), nullable=True),
        sa.Column('league_name', sa.String(length=100), nullable=True),
        sa.Column('kickoff_time', sa.DateTime(), nullable=True),
        sa.Column('ranking_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['fixture_id'], ['fixtures.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_analysis_fixture', 'analysis_history', ['fixture_id'])
    op.create_index('idx_analysis_created', 'analysis_history', ['created_at'])
    op.create_index('idx_analysis_confidence', 'analysis_history', ['confidence_score'])


def downgrade() -> None:
    """Remove FootyStats integration tables."""
    op.drop_index('idx_analysis_confidence', table_name='analysis_history')
    op.drop_index('idx_analysis_created', table_name='analysis_history')
    op.drop_index('idx_analysis_fixture', table_name='analysis_history')
    op.drop_table('analysis_history')

    op.drop_index('idx_team_footystats_id', table_name='team_id_mapping')
    op.drop_index('idx_team_api_id', table_name='team_id_mapping')
    op.drop_table('team_id_mapping')

    op.drop_index('idx_league_api_id', table_name='league_id_mapping')
    op.drop_table('league_id_mapping')
