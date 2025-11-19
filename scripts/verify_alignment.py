#!/usr/bin/env python3
"""Verify both databases are aligned"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

local_url = os.getenv('DATABASE_URL')
prod_url = os.getenv('DATABASE_URL_PRODUCTION')

def get_db_info(engine, name):
    with engine.connect() as conn:
        # Get tables
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = set(row[0] for row in result)

        # Get alembic version
        try:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
        except:
            version = None

        # Get row counts for key tables
        counts = {}
        for table in ['league_id_mapping', 'team_id_mapping']:
            if table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                counts[table] = result.scalar()

        return {
            'name': name,
            'tables': tables,
            'version': version,
            'counts': counts
        }

print("\n" + "="*70)
print("  🔍 VERIFICACIÓN DE ALINEACIÓN - LOCAL vs RAILWAY")
print("="*70 + "\n")

local_info = get_db_info(create_engine(local_url), "LOCAL")
prod_info = get_db_info(create_engine(prod_url), "RAILWAY")

# Compare tables
print("📊 TABLAS:")
print(f"  LOCAL:   {len(local_info['tables'])} tablas")
print(f"  RAILWAY: {len(prod_info['tables'])} tablas")

if local_info['tables'] == prod_info['tables']:
    print("  ✅ ALINEADAS - Mismas tablas en ambas BD")
else:
    only_local = local_info['tables'] - prod_info['tables']
    only_prod = prod_info['tables'] - local_info['tables']
    if only_local:
        print(f"  ❌ Solo en LOCAL: {only_local}")
    if only_prod:
        print(f"  ❌ Solo en RAILWAY: {only_prod}")

# Compare versions
print("\n🏷️  VERSIONES ALEMBIC:")
print(f"  LOCAL:   {local_info['version'] or '❌ Sin versión'}")
print(f"  RAILWAY: {prod_info['version'] or '❌ Sin versión'}")

if local_info['version'] == prod_info['version']:
    print("  ✅ ALINEADAS - Misma versión")
else:
    print(f"  ⚠️  DESALINEADAS")

# Compare data counts
print("\n📈 DATOS:")
print(f"  League mappings:")
print(f"    LOCAL:   {local_info['counts'].get('league_id_mapping', 0)} registros")
print(f"    RAILWAY: {prod_info['counts'].get('league_id_mapping', 0)} registros")

print(f"  Team mappings:")
print(f"    LOCAL:   {local_info['counts'].get('team_id_mapping', 0)} registros")
print(f"    RAILWAY: {prod_info['counts'].get('team_id_mapping', 0)} registros")

# Final verdict
print("\n" + "="*70)
if (local_info['tables'] == prod_info['tables'] and
    local_info['version'] == prod_info['version'] and
    local_info['counts'].get('league_id_mapping') == prod_info['counts'].get('league_id_mapping')):
    print("  ✅ BASES DE DATOS 100% ALINEADAS")
    print("="*70 + "\n")
    sys.exit(0)
else:
    print("  ⚠️  BASES DE DATOS CON DIFERENCIAS MENORES")
    print("="*70 + "\n")
    sys.exit(1)
