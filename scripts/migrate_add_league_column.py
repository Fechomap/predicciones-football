#!/usr/bin/env python3
"""
Migration: Add league_id column to team_id_mapping table
"""
import sys
import os
import psycopg2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.config import Config

def migrate():
    """Add league_id column to team_id_mapping"""
    print("\n" + "="*60)
    print("🔧 MIGRATING DATABASE - Add league_id to team_id_mapping")
    print("="*60 + "\n")

    try:
        # Connect to database
        conn = psycopg2.connect(Config.DATABASE_URL)
        cursor = conn.cursor()

        # Check if column exists
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='team_id_mapping'
            AND column_name='league_id'
        """)

        exists = cursor.fetchone()

        if exists:
            print("✅ Column league_id already exists\n")
        else:
            print("Adding league_id column...")

            # Add column
            cursor.execute("""
                ALTER TABLE team_id_mapping
                ADD COLUMN league_id INTEGER;
            """)

            conn.commit()
            print("✅ Column league_id added successfully\n")

        cursor.close()
        conn.close()

        print("="*60)
        print("✅ MIGRATION COMPLETED")
        print("="*60 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}\n")
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
