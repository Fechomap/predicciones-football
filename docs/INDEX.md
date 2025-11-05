# 📚 Índice de Documentación

Guía completa para desarrolladores del Football Betting Analytics Bot.

## 🗺️ Orden de Lectura Recomendado

### Para Nuevos Desarrolladores

1. **README.md** (raíz del proyecto)
   - Introducción general
   - Quick start
   - Estructura del proyecto

2. **[ARCHITECTURE.md](ARCHITECTURE.md)**
   - Arquitectura del sistema
   - Componentes principales
   - Flujo de datos

3. **[DEVELOPMENT.md](DEVELOPMENT.md)**
   - Setup del entorno de desarrollo
   - Convenciones de código
   - Cómo contribuir

### Para Deployment

4. **[DEPLOYMENT.md](DEPLOYMENT.md)**
   - Configuración de entornos
   - Gestión de base de datos
   - Scripts de deployment

5. **[RAILWAY_CONFIG.md](RAILWAY_CONFIG.md)**
   - Configuración específica de Railway
   - Variables de entorno para producción
   - Troubleshooting

## 📖 Documentos Disponibles

### Generales
- **README.md** - Introducción y quick start
- **ARCHITECTURE.md** - Arquitectura del sistema
- **DEVELOPMENT.md** - Guía de desarrollo

### Deployment
- **DEPLOYMENT.md** - Guía completa de deployment
- **RAILWAY_CONFIG.md** - Configuración Railway
- **DATABASE.md** - Gestión de base de datos

### Técnicos
- **API.md** - Documentación de APIs
- **TESTING.md** - Guía de testing
- **TROUBLESHOOTING.md** - Solución de problemas

### Investigación y Nuevas Features
- **[LIVE_PREDICTIONS_SUMMARY.md](LIVE_PREDICTIONS_SUMMARY.md)** - ⚡ Resumen ejecutivo: Predicciones en tiempo real
- **[LIVE_PREDICTIONS_RESEARCH.md](LIVE_PREDICTIONS_RESEARCH.md)** - 🔬 Investigación completa: Sistema de predicciones en vivo
- **[LIVE_PREDICTIONS_CODE_EXAMPLES.md](LIVE_PREDICTIONS_CODE_EXAMPLES.md)** - 💻 Ejemplos de código para implementación
- **[FOOTYSTATS_INTEGRATION_GUIDE.md](FOOTYSTATS_INTEGRATION_GUIDE.md)** - 🎯 Guía completa: Integración de FootyStats API (Córners)
- **[ALERT_SYSTEM_FIX.md](ALERT_SYSTEM_FIX.md)** - 🚨 Fix del sistema de alertas

## 🔍 Buscar por Tema

### Configuración
- [Variables de entorno](DEVELOPMENT.md#variables-de-entorno)
- [Configuración Railway](RAILWAY_CONFIG.md)
- [Base de datos](DATABASE.md)

### Desarrollo
- [Arquitectura](ARCHITECTURE.md)
- [Convenciones de código](DEVELOPMENT.md#convenciones)
- [Testing](TESTING.md)

### Deployment
- [Entornos múltiples](DEPLOYMENT.md#entornos)
- [Railway](RAILWAY_CONFIG.md)
- [Migraciones](DATABASE.md#migraciones)

## 🆘 ¿Necesitas Ayuda?

1. **Problemas comunes**: Ver [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. **Deployment**: Ver [DEPLOYMENT.md](DEPLOYMENT.md)
3. **Desarrollo**: Ver [DEVELOPMENT.md](DEVELOPMENT.md)

## 📝 Contribuir a la Documentación

Si encuentras información faltante o incorrecta:

1. Crea un issue describiendo el problema
2. O mejor, crea un PR con la corrección
3. Mantén el mismo formato y estructura

## 🆕 Nuevas Investigaciones

### 🔴 Predicciones en Tiempo Real (Live Predictions)

**Orden de lectura recomendado**:

1. **[LIVE_PREDICTIONS_SUMMARY.md](LIVE_PREDICTIONS_SUMMARY.md)** ⚡
   - Resumen ejecutivo (5 min lectura)
   - Viabilidad técnica y económica
   - Decisión: GO/NO GO

2. **[LIVE_PREDICTIONS_RESEARCH.md](LIVE_PREDICTIONS_RESEARCH.md)** 🔬
   - Investigación completa (20 min lectura)
   - Arquitectura propuesta
   - Plan de implementación por fases
   - Análisis de riesgos y costos

3. **[LIVE_PREDICTIONS_CODE_EXAMPLES.md](LIVE_PREDICTIONS_CODE_EXAMPLES.md)** 💻
   - Ejemplos de código concretos
   - Modelos de base de datos
   - Servicios y handlers
   - Listo para copiar y usar

**Estado**: 🟢 Listo para implementación

---

### 🎯 Integración FootyStats API (Córners y Estadísticas)

**Documento principal**:

**[FOOTYSTATS_INTEGRATION_GUIDE.md](FOOTYSTATS_INTEGRATION_GUIDE.md)** 🎯
- Guía completa de integración (1000+ líneas)
- Análisis comparativo con API-Football
- Arquitectura de integración complementaria
- Plan de implementación en 6 fases
- Ejemplos de código completos
- Modelos de base de datos
- Testing strategy
- Análisis de costos (£29.99/mes - Plan Hobby)

**Incluye**:
- ✅ Análisis de endpoints de córners
- ✅ CornerAnalyzer con distribución Poisson
- ✅ Detección de value bets en córners
- ✅ Sistema de cache y rate limiting
- ✅ Migración de base de datos
- ✅ Comandos Telegram (/corners_stats, /corner_trends)
- ✅ Métricas y monitoreo
- ✅ Checklist de implementación

**Estado**: 🟢 Listo para implementación

---

## 🔄 Última Actualización

**Fecha**: Noviembre 2025
**Versión**: 1.2.0
