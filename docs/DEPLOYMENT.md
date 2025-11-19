# 🚀 Guía de Deployment - Entornos Múltiples

Este proyecto soporta dos entornos: **Desarrollo** (local) y **Producción** (Railway).

## 📋 Configuración de Entornos

### Variables de Entorno

El archivo `.env` contiene:

```env
# Environment (development o production)
ENVIRONMENT=development

# Base de Datos Local
DATABASE_URL_LOCAL=postgresql://localhost:5432/football_betting

# Base de Datos Railway (Producción)
DATABASE_URL_PRODUCTION=postgresql://postgres:password@host:port/railway
```

## 🔄 Cambiar entre Entornos

### Opción 1: Script Automático (Recomendado)

```bash
# Cambiar a desarrollo (local)
./scripts/switch_env.sh dev

# Cambiar a producción (Railway)
./scripts/switch_env.sh prod
```

### Opción 2: Manual

Edita `.env` y cambia:
```env
ENVIRONMENT=development  # o production
```

## ✅ Verificar Conexión

```bash
# Probar conexión actual
python3 scripts/test_db.py
```

Muestra:
- Entorno activo
- URL de base de datos (parcial)
- Cantidad de fixtures y ligas

## 🗄️ Gestión de Base de Datos

### Primera Vez: Migrar a Producción

```bash
# Crear tablas en Railway
python3 scripts/migrate_to_production.py
```

Este script:
- ✅ Crea las 8 tablas necesarias
- ✅ Es idempotente (seguro ejecutar múltiples veces)
- ✅ NO borra datos existentes

### Tablas Creadas

1. **leagues** - Ligas de fútbol
2. **teams** - Equipos
3. **fixtures** - Partidos
4. **team_statistics** - Estadísticas por equipo
5. **odds_history** - Historial de cuotas
6. **predictions** - Predicciones del modelo
7. **value_bets** - Value bets detectados
8. **notifications_log** - Log de notificaciones

## 🎯 Workflow Recomendado

### Desarrollo Local

```bash
# 1. Cambiar a desarrollo
./scripts/switch_env.sh dev

# 2. Probar conexión
python3 scripts/test_db.py

# 3. Iniciar bot
./start.sh
```

### Deployment a Producción

```bash
# 1. Cambiar a producción
./scripts/switch_env.sh prod

# 2. Verificar conexión
python3 scripts/test_db.py

# 3. Si es primera vez, crear tablas
python3 scripts/migrate_to_production.py

# 4. Iniciar bot
./start.sh
```

## 🔒 Seguridad

- ✅ `.env` está en `.gitignore` (no se sube a Git)
- ✅ Usa `.env.example` como plantilla
- ✅ Nunca compartas credenciales de producción

## 📊 Estado Actual

### Local (Development)
- 📚 Database: PostgreSQL local
- 📊 Fixtures: ~56
- 📊 Ligas: 5

### Railway (Production)
- 📚 Database: Railway PostgreSQL
- 🔗 Host: trolley.proxy.rlwy.net
- ✅ Tablas creadas
- 📊 Fixtures: 4
- 📊 Ligas: 5

## ⚠️ Notas Importantes

1. **NO necesitas Alembic** para la primera instalación
2. **SQLAlchemy create_all()** es suficiente
3. Si cambias el esquema en el futuro, considera usar Alembic
4. Siempre prueba en desarrollo antes de producción

## 🆘 Troubleshooting

### Error de conexión a Railway
```bash
# Verificar que DATABASE_URL_PRODUCTION sea correcta
grep DATABASE_URL_PRODUCTION .env

# Probar conexión
./scripts/switch_env.sh prod
python3 scripts/test_db.py
```

### Tablas no existen
```bash
# Recrear tablas
python3 scripts/migrate_to_production.py
```

## 📝 Scripts Disponibles

- `scripts/switch_env.sh` - Cambiar entorno
- `scripts/test_db.py` - Probar conexión
- `scripts/migrate_to_production.py` - Migrar a Railway
- `verify_schema.py` - Ver esquema de tablas
- `start.sh` - Iniciar bot

