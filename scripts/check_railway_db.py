#!/usr/bin/env python3
"""Check Railway database status"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Get production URL
prod_url = os.getenv('DATABASE_URL_PRODUCTION')
if not prod_url:
    print("❌ DATABASE_URL_PRODUCTION not found in .env")
    sys.exit(1)

print(f"Conectando a Railway: {prod_url[:50]}...")

try:
    engine = create_engine(prod_url)

    with engine.connect() as conn:
        # Check tables
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]

        print(f"\n📊 Tablas en Railway ({len(tables)}):")
        for table in tables:
            print(f"  • {table}")

        # Check Alembic version
        if 'alembic_version' in tables:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            print(f"\n✅ Alembic version: {version if version else 'Sin versión'}")
        else:
            print("\n⚠️  Tabla 'alembic_version' NO existe")
            print("   La BD nunca ha sido migrada con Alembic")

        # Check if key tables exist
        required_tables = ['fixtures', 'teams', 'leagues', 'team_id_mapping', 'league_id_mapping']
        missing = [t for t in required_tables if t not in tables]

        if missing:
            print(f"\n⚠️  Tablas faltantes: {', '.join(missing)}")
        else:
            print("\n✅ Todas las tablas requeridas existen")

except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
