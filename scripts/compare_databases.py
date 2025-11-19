#!/usr/bin/env python3
"""Compare local and Railway databases"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

local_url = os.getenv('DATABASE_URL')
prod_url = os.getenv('DATABASE_URL_PRODUCTION')

def get_tables(engine):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        return set(row[0] for row in result)

def get_alembic_version(engine):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            return result.scalar()
    except:
        return None

print("\n" + "="*60)
print("  🔍 COMPARACIÓN DE BASES DE DATOS")
print("="*60 + "\n")

# Check local
print("📍 BASE DE DATOS LOCAL")
print("-" * 60)
local_engine = create_engine(local_url)
local_tables = get_tables(local_engine)
local_version = get_alembic_version(local_engine)

print(f"Tablas: {len(local_tables)}")
for table in sorted(local_tables):
    print(f"  • {table}")
print(f"\nAlembic version: {local_version or '❌ NO EXISTE'}")

# Check Railway
print("\n📍 BASE DE DATOS RAILWAY (PRODUCCIÓN)")
print("-" * 60)
prod_engine = create_engine(prod_url)
prod_tables = get_tables(prod_engine)
prod_version = get_alembic_version(prod_engine)

print(f"Tablas: {len(prod_tables)}")
for table in sorted(prod_tables):
    print(f"  • {table}")
print(f"\nAlembic version: {prod_version or '❌ NO EXISTE'}")

# Compare
print("\n" + "="*60)
print("  📊 ANÁLISIS DE DISCREPANCIAS")
print("="*60 + "\n")

only_local = local_tables - prod_tables
only_prod = prod_tables - local_tables
common = local_tables & prod_tables

if only_local:
    print(f"❌ Solo en LOCAL ({len(only_local)}):")
    for table in sorted(only_local):
        print(f"   • {table}")
else:
    print("✅ No hay tablas únicas en LOCAL")

if only_prod:
    print(f"\n❌ Solo en RAILWAY ({len(only_prod)}):")
    for table in sorted(only_prod):
        print(f"   • {table}")
else:
    print("\n✅ No hay tablas únicas en RAILWAY")

print(f"\n✅ Tablas comunes: {len(common)}")

# Version comparison
print("\n" + "="*60)
print("  🏷️  VERSIONADO ALEMBIC")
print("="*60)
print(f"\nLOCAL:   {local_version or '❌ Sin versión'}")
print(f"RAILWAY: {prod_version or '❌ Sin versión'}")

if local_version and prod_version:
    if local_version == prod_version:
        print("\n✅ Versiones ALINEADAS")
    else:
        print(f"\n⚠️  DESALINEADAS: Local={local_version}, Railway={prod_version}")
elif local_version and not prod_version:
    print("\n⚠️  LOCAL tiene Alembic, RAILWAY NO")
elif not local_version and prod_version:
    print("\n⚠️  RAILWAY tiene Alembic, LOCAL NO")
else:
    print("\n⚠️  Ninguna tiene Alembic configurado")

print("\n" + "="*60 + "\n")
