# 🚂 Configuración para Railway (Producción)

## ✅ Variables de Entorno para Railway

Copia y pega estas variables en el dashboard de Railway:

```env
# API-Football
RAPIDAPI_KEY=19cd24b30b1bc9652cecbf0eafa34875
RAPIDAPI_HOST=api-football-v1.p.rapidapi.com

# Telegram Bot (Producción)
TELEGRAM_BOT_TOKEN=8158522572:AAG73ll2OWEiPB_jl8eq58Fz21mUbSE3m7Q
TELEGRAM_CHAT_ID=allow

# Environment (IMPORTANTE: debe ser "production")
ENVIRONMENT=production

# Database (Railway configura esto automáticamente)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Bot Configuration
ALERT_TIME_MINUTES=60
MINIMUM_EDGE=0.05
CHECK_INTERVAL=30
ENABLED_LEAGUES=262,39,140,78,135
MIN_CONFIDENCE=3
MAX_ALERTS_PER_DAY=10

# Server
PORT=8000

# Logging
LOG_LEVEL=INFO
```

## 🔧 Cómo Configurar en Railway

### 1. Variables a Modificar

**Antes** (incorrecto):
```env
RAILWAY_ENVIRONMENT=development  ❌ Eliminar esta línea
```

**Después** (correcto):
```env
ENVIRONMENT=production  ✅ Agregar esta línea
```

### 2. Pasos en Railway Dashboard

1. Ve a tu proyecto en Railway
2. Click en tu servicio
3. Pestaña "Variables"
4. **Elimina**: `RAILWAY_ENVIRONMENT`
5. **Agrega**: `ENVIRONMENT` con valor `production`
6. Guarda los cambios
7. Railway redesplegará automáticamente

### 3. Verificar Configuración

Después del redespliegue, verifica los logs:
```
✅ Debe mostrar: "🔧 Using pre-configured DATABASE_URL"
✅ El bot debe conectarse a Railway PostgreSQL
✅ Debe mostrar: "✅ Database connected"
```

## 🎯 Diferencias entre Desarrollo y Producción

| Variable | Desarrollo (Local) | Producción (Railway) |
|----------|-------------------|----------------------|
| `ENVIRONMENT` | `development` | `production` |
| `TELEGRAM_BOT_TOKEN` | Bot de prueba | Bot de producción |
| `DATABASE_URL` | `postgresql://localhost:5432/...` | `${{Postgres.DATABASE_URL}}` |
| `ALERT_TIME_MINUTES` | 60 | 60 |
| `CHECK_INTERVAL` | 30 | 30 |

## ⚠️ Importante

1. **NO copies `DATABASE_URL_LOCAL`** a Railway (no es necesario)
2. **NO copies `DATABASE_URL_PRODUCTION`** a Railway (no es necesario)
3. Railway usa `${{Postgres.DATABASE_URL}}` que es una referencia al servicio PostgreSQL
4. El código detecta automáticamente si ya está configurado y lo usa

## 🧪 Probar Configuración

Una vez desplegado, verifica en los logs de Railway:

```
🔧 Using pre-configured DATABASE_URL
✅ Database connected
✅ Database tables ready
✅ Telegram connected
🚀 Bot is now running!
```

## 🆘 Troubleshooting

### Problema: "DATABASE_URL_PRODUCTION not configured"

**Causa**: Falta `DATABASE_URL` en Railway

**Solución**: Agrega `DATABASE_URL=${{Postgres.DATABASE_URL}}`

### Problema: "Using LOCAL database" en producción

**Causa**: `ENVIRONMENT` no está configurado o está en "development"

**Solución**: Configura `ENVIRONMENT=production`

### Problema: Error de conexión a BD

**Causa**: Railway Postgres no está conectado

**Solución**: 
1. Ve a tu servicio en Railway
2. Click en "Connect" 
3. Selecciona "Postgres"
4. Guarda y redesplega

