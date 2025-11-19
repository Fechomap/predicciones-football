#!/usr/bin/env python3
"""Migrate database schema to production (Railway)"""
import sys
import os

# Force production environment
os.environ['ENVIRONMENT'] = 'production'

from src.utils.config import Config
from src.database.connection import db_manager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def migrate_to_production():
    """Create database tables in production"""
    print("\n" + "="*60)
    print("🚀 MIGRACIÓN A PRODUCCIÓN (RAILWAY)")
    print("="*60 + "\n")
    
    print(f"📍 Entorno: {Config.ENVIRONMENT}")
    print(f"📚 Database: {Config.DATABASE_URL[:70]}...")
    print()
    
    response = input("⚠️  ¿Estás seguro de crear las tablas en PRODUCCIÓN? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Operación cancelada")
        return False
    
    print("\n🔨 Creando tablas en Railway PostgreSQL...")

    try:
        # Initialize database and create tables
        db_manager.initialize()
        db_manager.create_tables()
        print("✅ Conexión exitosa a Railway")
        print("✅ Tablas creadas correctamente en producción")
        print()
        print("🎉 ¡Migración completada!")
        return True
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_to_production()
    sys.exit(0 if success else 1)
