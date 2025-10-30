#!/usr/bin/env python3
"""Test database connection"""
import sys
from src.utils.config import Config
from src.database.connection import db_manager

def test_connection():
    """Test database connection"""
    print("\n" + "="*50)
    print("🔍 PROBANDO CONEXIÓN A BASE DE DATOS")
    print("="*50 + "\n")

    print(f"Entorno: {Config.ENVIRONMENT}")
    print(f"Database URL: {Config.DATABASE_URL[:70]}...")
    print()

    try:
        db_manager.initialize()
        print("✅ Conexión exitosa!")

        # Try to count fixtures
        with db_manager.get_session() as session:
            from src.database.models import Fixture, League
            fixtures_count = session.query(Fixture).count()
            leagues_count = session.query(League).count()
            print(f"📊 Fixtures en BD: {fixtures_count}")
            print(f"📊 Ligas en BD: {leagues_count}")

        return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
