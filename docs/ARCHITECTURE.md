# 🏗️ Arquitectura del Sistema

## 📊 Visión General

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Bot                          │
│              (Interface del Usuario)                     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  Bot Service                             │
│         (Orquestación y Lógica de Negocio)              │
└──┬───────────┬───────────┬──────────────┬──────────────┘
   │           │           │              │
   ▼           ▼           ▼              ▼
┌────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────┐
│   API  │ │Analyzers│ │ Database │ │ Notifications│
│Football│ │(Poisson)│ │(Postgres)│ │  (Telegram)  │
└────────┘ └─────────┘ └──────────┘ └──────────────┘
```

## 🔧 Componentes Principales

### 1. API Layer (`src/api/`)

**Responsabilidad**: Comunicación con API-Football

- `api_football.py` - Cliente HTTP con rate limiting
- `rate_limiter.py` - Control de límites de API

**Funciones clave**:
- Obtener fixtures (partidos)
- Obtener estadísticas de equipos
- Obtener predicciones de la API
- Obtener odds (cuotas)

### 2. Analyzers (`src/analyzers/`)

**Responsabilidad**: Análisis estadístico y detección de value

- `poisson_analyzer.py` - Modelo de Poisson para predicciones
- `form_analyzer.py` - Análisis de forma de equipos
- `value_detector.py` - Detección de value bets

**Proceso**:
1. Calcula goles esperados usando Poisson
2. Determina probabilidades de resultado
3. Compara con odds del mercado
4. Identifica value bets (edge positivo)

### 3. Database (`src/database/`)

**Responsabilidad**: Persistencia de datos

- `models.py` - Modelos SQLAlchemy
- `connection.py` - Gestión de conexiones

**Tablas**:
- `leagues` - Ligas monitoreadas
- `teams` - Equipos
- `fixtures` - Partidos
- `team_statistics` - Estadísticas
- `odds_history` - Historial de cuotas
- `predictions` - Predicciones generadas
- `value_bets` - Value bets detectados
- `notifications_log` - Registro de notificaciones

### 4. Services (`src/services/`)

**Responsabilidad**: Lógica de negocio

- `bot_service.py` - Orquestador principal
- `data_collector.py` - Recolección de datos
- `fixtures_service.py` - Gestión de fixtures con cache
- `scheduler.py` - Tareas programadas

**Flujo**:
1. Recolectar fixtures próximos
2. Analizar cada fixture
3. Detectar value bets
4. Enviar notificaciones

### 5. Notifications (`src/notifications/`)

**Responsabilidad**: Comunicación con usuario

- `telegram_bot.py` - Bot de Telegram
- `telegram_commands.py` - Comandos del bot
- `telegram_handlers.py` - Manejadores de callbacks
- `telegram_menu.py` - Menús interactivos
- `message_formatter.py` - Formato de mensajes

## 🔄 Flujo de Datos

### Ciclo de Monitoreo Automático

```
1. Scheduler (cada 30 min)
   ↓
2. Bot Service: check_fixtures()
   ↓
3. Data Collector: collect_upcoming_fixtures()
   ↓
4. Fixtures Service: get_upcoming_fixtures()
   ├─→ BD (cache) si < 1h
   └─→ API si > 1h o force_refresh
   ↓
5. Para cada fixture:
   ├─→ Obtener estadísticas (API)
   ├─→ Obtener odds (API)
   ├─→ Calcular predicción (Poisson)
   ├─→ Detectar value bet
   └─→ Si hay value: notificar
```

### Flujo de Usuario (Telegram)

```
1. Usuario presiona "⚽ Fútbol"
   ↓
2. Telegram Handler
   ↓
3. Fixtures Service: get_upcoming_fixtures(force_refresh=False)
   ↓
4. Retorna desde BD (instantáneo)
   ↓
5. Usuario selecciona partido
   ↓
6. Analizar partido
   ├─→ Obtener predicciones API
   ├─→ Calcular Poisson
   ├─→ Detectar value
   └─→ Mostrar análisis
```

## 🎯 Optimizaciones Clave

### 1. Cache de Base de Datos

**Problema**: Cada interacción del usuario hacía llamadas API

**Solución**:
- Fixtures se almacenan en PostgreSQL
- Lecturas desde BD (instantáneo)
- API solo en ciclo automático

**Resultado**: 95% reducción en llamadas API

### 2. Fixtures Service

**Estrategia**:
```python
force_refresh=False  # Usuario navegando
→ Lee BD directamente (rápido)

force_refresh=True   # Ciclo automático
→ Llama API y actualiza BD
```

### 3. Rate Limiting

**Configuración**:
- Límite: 250 requests/minuto
- Plan API: 300 requests/minuto
- Margen de seguridad: 50 requests

## 🔐 Configuración Multi-Entorno

### Development
```
ENVIRONMENT=development
DATABASE_URL → Local PostgreSQL
TELEGRAM_BOT_TOKEN → Bot de prueba
```

### Production
```
ENVIRONMENT=production  
DATABASE_URL → Railway PostgreSQL
TELEGRAM_BOT_TOKEN → Bot de producción
```

**Auto-detección**:
El sistema detecta automáticamente el entorno y configura las conexiones apropiadas.

## 📈 Escalabilidad

### Actual
- 1 instancia
- PostgreSQL Railway
- 48 llamadas API/día (ciclo cada 30 min)

### Posibles Mejoras
- [ ] Horizontal scaling con múltiples workers
- [ ] Redis para cache distribuido
- [ ] WebSocket para updates en tiempo real
- [ ] API GraphQL para frontend web

## 🧪 Testing

### Unit Tests
- `tests/analyzers/` - Tests de modelo Poisson
- `tests/services/` - Tests de lógica de negocio

### Integration Tests
- Conexión BD
- API calls
- Telegram bot

## 🔍 Monitoreo

### Logs
- Railway Dashboard para producción
- Console para desarrollo
- Nivel configurable (DEBUG, INFO, WARNING, ERROR)

### Métricas Importantes
- API calls por hora
- Value bets detectados
- Notificaciones enviadas
- Errores y excepciones
