#!/usr/bin/env python3
"""
Limpia mapeos de baja confianza de TeamIDMapping

OBJETIVO:
- Eliminar mapeos con confianza <95%
- Preparar BD para re-mapeo correcto
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import db_manager, TeamIDMapping
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

CONFIDENCE_THRESHOLD = 0.95  # Solo mantener mapeos con confianza ≥95% (0.95 en escala 0-1)


def clean_low_confidence_mappings():
    """Elimina mapeos de baja confianza"""

    print("\n" + "="*70)
    print("  🧹 LIMPIEZA DE MAPEOS DE BAJA CONFIANZA")
    print("="*70)

    try:
        db_manager.initialize()

        with db_manager.get_session() as session:
            # 1. Contar total de mapeos actuales
            total_mappings = session.query(TeamIDMapping).count()
            print(f"\n📊 Mapeos actuales: {total_mappings}")

            # 2. Contar mapeos de alta confianza (≥95%)
            high_confidence = session.query(TeamIDMapping).filter(
                TeamIDMapping.confidence_score >= CONFIDENCE_THRESHOLD
            ).count()

            # 3. Contar mapeos de baja confianza (<95%)
            low_confidence = session.query(TeamIDMapping).filter(
                TeamIDMapping.confidence_score < CONFIDENCE_THRESHOLD
            ).count()

            # 4. Contar mapeos con footystats_id NULL
            null_mappings = session.query(TeamIDMapping).filter(
                TeamIDMapping.footystats_id.is_(None)
            ).count()

            print(f"\n📈 Estadísticas:")
            print(f"   ✅ Alta confianza (≥{CONFIDENCE_THRESHOLD}%): {high_confidence}")
            print(f"   ⚠️  Baja confianza (<{CONFIDENCE_THRESHOLD}%): {low_confidence}")
            print(f"   ❌ IDs nulos: {null_mappings}")

            # 5. Confirmar eliminación
            to_delete = low_confidence + null_mappings
            if to_delete == 0:
                print("\n✅ No hay mapeos para eliminar. BD limpia.")
                return True

            print(f"\n⚠️  Se eliminarán {to_delete} mapeos incorrectos")
            print(f"   Se mantendrán {high_confidence} mapeos de alta confianza")

            # Confirmar (en producción, esto debería pedir confirmación)
            print("\n🔄 Eliminando mapeos de baja confianza...")

            # 6. Eliminar mapeos de baja confianza
            deleted_low = session.query(TeamIDMapping).filter(
                TeamIDMapping.confidence_score < CONFIDENCE_THRESHOLD
            ).delete()

            # 7. Eliminar mapeos con ID nulo
            deleted_null = session.query(TeamIDMapping).filter(
                TeamIDMapping.footystats_id.is_(None)
            ).delete()

            session.commit()

            print(f"\n✅ Eliminados:")
            print(f"   - {deleted_low} mapeos de baja confianza")
            print(f"   - {deleted_null} mapeos con ID nulo")
            print(f"\n✅ Mantenidos: {high_confidence} mapeos de alta confianza")

            # 8. Verificar
            remaining = session.query(TeamIDMapping).count()
            print(f"\n📊 Mapeos restantes: {remaining}")

            if remaining == high_confidence:
                print("✅ Limpieza completada correctamente")
                return True
            else:
                print("⚠️  Discrepancia detectada, verificar manualmente")
                return False

    except Exception as e:
        logger.error(f"Error durante limpieza: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚨 ADVERTENCIA: Este script eliminará mapeos de baja confianza")
    print("   Solo se mantendrán mapeos con confianza ≥95%")
    print()

    # En producción, descomentar esto para pedir confirmación
    # response = input("¿Continuar? (yes/no): ")
    # if response.lower() != "yes":
    #     print("Operación cancelada")
    #     sys.exit(0)

    success = clean_low_confidence_mappings()
    sys.exit(0 if success else 1)
