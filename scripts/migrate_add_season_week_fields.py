#!/usr/bin/env python3
"""
Migration script: Add season, week, last_updated fields to Fixture model
Also adds pdf_url and confidence_score for analysis history

This migration supports:
- Season-long fixture storage
- Weekly calendar filtering
- PDF report storage
- Analysis confidence ranking
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.database.connection import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database connection
db_manager.initialize()


def migrate_up():
    """Add new fields to fixtures table"""
    engine = db_manager.engine

    migrations = [
        # Add season field (YYYY format)
        """
        ALTER TABLE fixtures
        ADD COLUMN IF NOT EXISTS season INTEGER;
        """,

        # Add week/matchday field (extracted from round field)
        """
        ALTER TABLE fixtures
        ADD COLUMN IF NOT EXISTS week INTEGER;
        """,

        # Add last_updated field (replaces created_at for freshness checks)
        """
        ALTER TABLE fixtures
        ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        """,

        # Add is_archived flag (for completed matches)
        """
        ALTER TABLE fixtures
        ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;
        """,

        # Add indexes for performance
        """
        CREATE INDEX IF NOT EXISTS idx_fixtures_season_week
        ON fixtures(season, week);
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_fixtures_status
        ON fixtures(status);
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_fixtures_kickoff
        ON fixtures(kickoff_time);
        """,
    ]

    logger.info("🚀 Starting migration: Add season/week fields to fixtures")

    with engine.connect() as conn:
        for i, migration_sql in enumerate(migrations, 1):
            try:
                logger.info(f"  [{i}/{len(migrations)}] Executing migration...")
                conn.execute(text(migration_sql))
                conn.commit()
                logger.info(f"  ✅ Migration {i} completed")
            except Exception as e:
                logger.error(f"  ❌ Migration {i} failed: {e}")
                raise

    logger.info("✅ All migrations completed successfully!")


def create_analysis_history_table():
    """Create new table for storing PDF analysis history"""
    engine = db_manager.engine

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS analysis_history (
        id SERIAL PRIMARY KEY,
        fixture_id INTEGER NOT NULL REFERENCES fixtures(id),
        pdf_url TEXT,
        pdf_cloudflare_key TEXT,
        confidence_score NUMERIC(5, 2),
        analysis_type VARCHAR(50) DEFAULT 'complete',

        -- Analysis data snapshot (for historical reference)
        home_team_name VARCHAR(100),
        away_team_name VARCHAR(100),
        league_name VARCHAR(100),
        kickoff_time TIMESTAMP,

        -- Predictions snapshot
        home_probability NUMERIC(5, 2),
        draw_probability NUMERIC(5, 2),
        away_probability NUMERIC(5, 2),
        recommended_bet VARCHAR(50),
        edge NUMERIC(5, 2),

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_analysis_history_fixture
    ON analysis_history(fixture_id);

    CREATE INDEX IF NOT EXISTS idx_analysis_history_confidence
    ON analysis_history(confidence_score DESC);

    CREATE INDEX IF NOT EXISTS idx_analysis_history_created
    ON analysis_history(created_at DESC);
    """

    logger.info("🚀 Creating analysis_history table...")

    with engine.connect() as conn:
        try:
            conn.execute(text(create_table_sql))
            conn.commit()
            logger.info("✅ analysis_history table created successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to create analysis_history table: {e}")
            raise


def populate_season_week_from_existing_data():
    """
    Populate season and week fields from existing fixture data
    Extracts week from round field (e.g., "Regular Season - 15" -> week=15)
    """
    with db_manager.get_session() as session:
        # Get all fixtures with round data
        result = session.execute(text("""
            SELECT id, round, kickoff_time
            FROM fixtures
            WHERE season IS NULL
        """))

        fixtures = result.fetchall()
        logger.info(f"📊 Found {len(fixtures)} fixtures to update")

        updated = 0
        for fixture in fixtures:
            fixture_id, round_str, kickoff_time = fixture

            # Extract season from kickoff_time (year)
            season = kickoff_time.year if kickoff_time else 2025

            # Extract week from round string
            week = None
            if round_str:
                # Try to extract number from strings like:
                # "Regular Season - 15" -> 15
                # "Matchday 10" -> 10
                # "Week 5" -> 5
                import re
                match = re.search(r'(\d+)', round_str)
                if match:
                    week = int(match.group(1))

            # Update fixture
            session.execute(text("""
                UPDATE fixtures
                SET season = :season,
                    week = :week,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = :fixture_id
            """), {
                'season': season,
                'week': week,
                'fixture_id': fixture_id
            })

            updated += 1

            if updated % 50 == 0:
                logger.info(f"  ... updated {updated}/{len(fixtures)} fixtures")

        logger.info(f"✅ Updated {updated} fixtures with season/week data")


def migrate_down():
    """Rollback migration (for testing purposes)"""
    engine = db_manager.engine

    rollback_sql = """
    ALTER TABLE fixtures DROP COLUMN IF EXISTS season;
    ALTER TABLE fixtures DROP COLUMN IF EXISTS week;
    ALTER TABLE fixtures DROP COLUMN IF EXISTS last_updated;
    ALTER TABLE fixtures DROP COLUMN IF EXISTS is_archived;

    DROP INDEX IF EXISTS idx_fixtures_season_week;
    DROP INDEX IF EXISTS idx_fixtures_status;
    DROP INDEX IF EXISTS idx_fixtures_kickoff;

    DROP TABLE IF EXISTS analysis_history CASCADE;
    """

    logger.info("⚠️  Rolling back migration...")

    with engine.connect() as conn:
        conn.execute(text(rollback_sql))
        conn.commit()

    logger.info("✅ Rollback completed")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Database migration for season/week fields')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()

    try:
        if args.rollback:
            migrate_down()
        else:
            migrate_up()
            create_analysis_history_table()
            populate_season_week_from_existing_data()

            logger.info("")
            logger.info("=" * 60)
            logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            logger.info("")
            logger.info("New fields added to fixtures table:")
            logger.info("  • season (INTEGER) - e.g., 2025")
            logger.info("  • week (INTEGER) - e.g., 15")
            logger.info("  • last_updated (TIMESTAMP) - for cache invalidation")
            logger.info("  • is_archived (BOOLEAN) - for historical data")
            logger.info("")
            logger.info("New table created:")
            logger.info("  • analysis_history - stores PDF reports and rankings")
            logger.info("")
            logger.info("Next steps:")
            logger.info("  1. Update models.py to reflect new schema")
            logger.info("  2. Run full season fixture load")
            logger.info("  3. Implement PDF generation")
            logger.info("")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)
