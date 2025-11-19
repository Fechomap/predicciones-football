#!/usr/bin/env python3
"""
Migración: Agregar columna analysis_data a tabla analysis_history

Esta columna almacenará el JSON completo del análisis para cache
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import db_manager
from sqlalchemy import text

def migrate():
    """Agrega columna analysis_data"""

    print("\n" + "="*70)
    print("  🔧 MIGRACIÓN: Agregar analysis_data a analysis_history")
    print("="*70)

    db_manager.initialize()

    with db_manager.get_session() as session:
        try:
            # Verificar si la columna ya existe
            result = session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='analysis_history'
                AND column_name='analysis_data';
            """))

            if result.fetchone():
                print("\n✅ La columna 'analysis_data' ya existe")
                return True

            # Agregar columna
            print("\n🔄 Agregando columna 'analysis_data' (TEXT)...")
            session.execute(text("""
                ALTER TABLE analysis_history
                ADD COLUMN analysis_data TEXT;
            """))

            session.commit()
            print("✅ Columna agregada exitosamente")

            # Verificar
            result = session.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name='analysis_history'
                ORDER BY ordinal_position;
            """))

            print("\n📋 Columnas de analysis_history:")
            for row in result:
                print(f"   - {row[0]:30} ({row[1]})")

            return True

        except Exception as e:
            print(f"\n❌ Error: {e}")
            session.rollback()
            return False


if __name__ == "__main__":
    success = migrate()
    print("\n" + "="*70 + "\n")
    sys.exit(0 if success else 1)
