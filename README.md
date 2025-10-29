# ⚽ Football Betting Analytics Bot

Bot automatizado de análisis estadístico para apuestas deportivas con notificaciones en Telegram. Analiza partidos de fútbol usando datos reales de API-Football y envía alertas de oportunidades de value bets.

---

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características](#-características)
- [Stack Tecnológico](#-stack-tecnológico)
- [Arquitectura](#-arquitectura)
- [Funcionamiento](#-funcionamiento)
- [Ligas Soportadas](#-ligas-soportadas)
- [Configuración](#-configuración)
- [Deployment en Railway](#-deployment-en-railway)
- [Variables de Entorno](#-variables-de-entorno)
- [Estructura del Proyecto](#-estructura-del-proyecto)

---

## 🎯 Descripción

Sistema automatizado que:
1. **Recopila** datos de partidos en tiempo real desde API-Football
2. **Analiza** estadísticas usando modelos matemáticos puros (sin IA/ML)
3. **Detecta** oportunidades de value bets comparando probabilidades
4. **Notifica** vía Telegram 1 hora antes del partido (o 10 minutos si no es posible)
5. **Se despliega** en Railway para ejecución 24/7

### ¿Por qué NO usamos IA/Machine Learning?

**Usamos análisis estadístico puro porque:**
- ✅ Trabajamos con datos reales y verificables
- ✅ Las estadísticas son más confiables que predicciones de IA
- ✅ Menor complejidad y más fácil de auditar
- ✅ No requiere entrenamiento ni grandes datasets
- ✅ Resultados consistentes y explicables

**Métodos estadísticos que usaremos:**
- Distribución de Poisson para goles esperados
- Análisis de racha y forma del equipo
- Comparación de cuotas implícitas vs probabilidades calculadas
- Análisis de valor esperado (EV)

---

## ✨ Características

### Core Features
- 🔄 **Monitoreo continuo** de partidos próximos
- 📊 **Análisis estadístico** basado en datos históricos reales
- 💰 **Detección de value bets** (edge > 5%)
- ⏰ **Alertas tempranas** (1 hora antes o 10 minutos mínimo)
- 📱 **Notificaciones Telegram** formateadas y claras
- 🗄️ **Base de datos PostgreSQL** para históricos
- ☁️ **Deploy en Railway** (ejecución continua)

### Ligas Prioritarias
- 🇲🇽 **Liga MX** (México)
- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 **Premier League** (Inglaterra)
- 🇪🇸 **La Liga** (España)
- 🇩🇪 **Bundesliga** (Alemania)
- ⚽ *Más ligas configurables*

---

## 🛠️ Stack Tecnológico

```
Backend: Python 3.11+
├── requests          # HTTP client para API-Football
├── python-telegram-bot # Bot de Telegram
├── psycopg2-binary   # PostgreSQL adapter
├── SQLAlchemy        # ORM
├── pandas            # Análisis de datos
├── numpy             # Cálculos numéricos
├── scipy             # Estadística (Poisson)
├── APScheduler       # Tareas programadas
└── python-dotenv     # Variables de entorno

Database: PostgreSQL 15
├── Almacenamiento de partidos
├── Histórico de estadísticas
├── Cuotas y predicciones
└── Log de notificaciones

Infrastructure: Railway
├── Deployment automático desde Git
├── PostgreSQL managed
├── Logs centralizados
└── Escalado automático
```

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────┐
│           API-FOOTBALL                      │
│  https://api-football-v1.p.rapidapi.com     │
│                                             │
│  Endpoints usados:                          │
│  - GET /v3/fixtures (partidos próximos)    │
│  - GET /v3/fixtures/statistics             │
│  - GET /v3/odds (cuotas)                   │
│  - GET /v3/standings (tabla posiciones)    │
│  - GET /v3/teams/statistics                │
└──────────────┬──────────────────────────────┘
               │
               ↓ (Requests cada 30 min)
               │
┌──────────────┴──────────────────────────────┐
│         PYTHON BOT (Railway)                │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  1. Data Collector Service           │  │
│  │     - Fetch fixtures próximos        │  │
│  │     - Rate limiting (10 req/min)     │  │
│  │     - Cache de datos                 │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  2. Statistical Analyzer             │  │
│  │     ┌─────────────────────────────┐  │  │
│  │     │ Poisson Distribution        │  │  │
│  │     │ (Goles esperados)           │  │  │
│  │     └─────────────────────────────┘  │  │
│  │     ┌─────────────────────────────┐  │  │
│  │     │ Form Analysis               │  │  │
│  │     │ (Últimos 5 partidos)        │  │  │
│  │     └─────────────────────────────┘  │  │
│  │     ┌─────────────────────────────┐  │  │
│  │     │ Head-to-Head Stats          │  │  │
│  │     └─────────────────────────────┘  │  │
│  │     ┌─────────────────────────────┐  │  │
│  │     │ Home/Away Performance       │  │  │
│  │     └─────────────────────────────┘  │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  3. Value Bet Detector               │  │
│  │     - Calcula probabilidades reales  │  │
│  │     - Compara con odds implícitas    │  │
│  │     - Identifica edge > 5%           │  │
│  │     - Filtra por confianza           │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  4. Notification Manager             │  │
│  │     - Scheduler (1h antes o 10min)   │  │
│  │     - Formateador de mensajes        │  │
│  │     - Retry logic                    │  │
│  └──────────────────────────────────────┘  │
└──────────────┬──────────────────────────────┘
               │
               ↓ (Telegram Bot API)
               │
┌──────────────┴──────────────────────────────┐
│          TELEGRAM BOT                       │
│                                             │
│  Envía notificaciones:                      │
│  ┌──────────────────────────────────────┐  │
│  │  ⚽ OPORTUNIDAD DETECTADA             │  │
│  │                                       │  │
│  │  🏆 Liga MX                           │  │
│  │  📅 América vs Guadalajara            │  │
│  │  🕐 Inicio: 20:00 hrs (1h)            │  │
│  │                                       │  │
│  │  📊 Análisis:                         │  │
│  │  • Prob. calculada: 65%              │  │
│  │  • Cuota: 1.85 (prob. 54%)           │  │
│  │  • Value Edge: +11%                  │  │
│  │  • Confianza: Alta                   │  │
│  │                                       │  │
│  │  💡 Recomendación: Local              │  │
│  │  💰 Stake sugerido: 3% bankroll      │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
               ↑
               │
        [Usuario recibe alerta]

┌─────────────────────────────────────────────┐
│       POSTGRESQL DATABASE                   │
│                                             │
│  Tables:                                    │
│  ├── leagues (ligas configuradas)          │
│  ├── teams (equipos)                       │
│  ├── fixtures (partidos)                   │
│  ├── team_statistics (stats históricas)    │
│  ├── odds_history (histórico de cuotas)    │
│  ├── predictions (análisis guardados)      │
│  ├── notifications_log (alertas enviadas)  │
│  └── value_bets (oportunidades detectadas) │
└─────────────────────────────────────────────┘
```

---

## ⚙️ Funcionamiento

### 1. Ciclo de Monitoreo (cada 30 minutos)

```python
# Pseudocódigo del ciclo principal
while True:
    # 1. Obtener partidos próximos (siguiente 72 horas)
    fixtures = api_football.get_upcoming_fixtures(leagues=['Liga MX'])

    # 2. Para cada partido que inicia en 60-90 minutos
    for fixture in fixtures:
        if 60 <= minutes_until_kickoff(fixture) <= 90:

            # 3. Recopilar estadísticas
            stats = collect_statistics(fixture)

            # 4. Análisis estadístico
            analysis = statistical_analyzer.analyze(stats)

            # 5. Detectar value bet
            if analysis.edge > 0.05:  # 5% mínimo

                # 6. Enviar notificación
                telegram.send_alert(analysis)

                # 7. Guardar en BD
                db.save_prediction(analysis)

    sleep(1800)  # 30 minutos
```

### 2. Análisis Estadístico

#### a) Distribución de Poisson para Goles Esperados

```python
# Ejemplo simplificado
def calculate_expected_goals(team_home, team_away):
    # Promedio de goles del equipo local en casa
    home_avg = team_home.goals_scored_home / team_home.matches_home

    # Promedio de goles concedidos por visitante fuera
    away_def = team_away.goals_conceded_away / team_away.matches_away

    # Liga promedio
    league_avg = get_league_average()

    # Fuerza ofensiva ajustada
    home_attack_strength = home_avg / league_avg
    away_defense_strength = away_def / league_avg

    # Goles esperados usando Poisson
    expected_goals = home_attack_strength * away_defense_strength * league_avg

    return expected_goals
```

#### b) Value Bet Detection

```python
def detect_value_bet(calculated_probability, bookmaker_odds):
    # Probabilidad implícita de la casa de apuestas
    implied_probability = 1 / bookmaker_odds

    # Edge (ventaja)
    edge = (calculated_probability * bookmaker_odds) - 1

    # Es value bet si edge > 5%
    if edge > 0.05:
        return {
            'is_value': True,
            'edge': edge,
            'expected_value': calculated_probability * bookmaker_odds
        }

    return {'is_value': False}
```

### 3. Sistema de Alertas

**Prioridad de tiempo:**
1. **Ideal**: 60 minutos antes del partido
2. **Fallback**: 10 minutos antes si no se detectó a tiempo
3. **Filtro**: No enviar si ya pasó el kickoff

**Formato de notificación:**
```
⚽ OPORTUNIDAD DETECTADA

🏆 Liga: Liga MX
📅 Partido: Club América vs Chivas Guadalajara
🕐 Inicio: 21:00 hrs (en 60 minutos)
🏟️ Estadio: Azteca

📊 ANÁLISIS ESTADÍSTICO

Resultado recomendado: Victoria Local (1)

🎯 Probabilidades:
• Calculada: 62.5%
• Casa de apuestas: 1.75 (prob. 57.1%)
• Value Edge: +5.4%

📈 Factores clave:
• América: 4W-1D últimos 5 (casa)
• Chivas: 1W-2D-2L últimos 5 (fuera)
• H2H: 3-1-1 favor América (últimos 5)
• Goles esperados: 1.85 vs 0.92

💰 RECOMENDACIÓN
• Confianza: Alta (★★★★☆)
• Stake sugerido: 3% del bankroll
• Expected Value: +9.45%

⚠️ Disclaimer: Análisis estadístico. Apuesta responsable.
```

---

## 🌍 Ligas Soportadas

### Configuración Inicial (Priority)

| Liga | ID API-Football | País | Prioridad |
|------|----------------|------|-----------|
| Liga MX (Apertura/Clausura) | 262 | 🇲🇽 México | ⭐⭐⭐⭐⭐ |
| Premier League | 39 | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra | ⭐⭐⭐⭐ |
| La Liga | 140 | 🇪🇸 España | ⭐⭐⭐⭐ |
| Bundesliga | 78 | 🇩🇪 Alemania | ⭐⭐⭐ |
| Serie A | 135 | 🇮🇹 Italia | ⭐⭐⭐ |
| Ligue 1 | 61 | 🇫🇷 Francia | ⭐⭐⭐ |

### Expandible a:
- Champions League
- Europa League
- Copa Libertadores
- MLS
- Liga Argentina
- Liga Brasileña

---

## 🚀 Configuración

### 1. Prerrequisitos

```bash
# Python 3.11+
python --version

# PostgreSQL 15+
psql --version

# Cuenta en API-Football
# https://www.api-football.com/

# Bot de Telegram creado
# https://t.me/BotFather
```

### 2. Variables de Entorno

Crear archivo `.env`:

```env
# API-Football
RAPIDAPI_KEY=your_rapidapi_key_here
RAPIDAPI_HOST=api-football-v1.p.rapidapi.com

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# PostgreSQL (Railway auto-genera estas)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Configuración Bot
ALERT_TIME_MINUTES=60  # Minutos antes del partido
MINIMUM_EDGE=0.05      # 5% mínimo value edge
CHECK_INTERVAL=30      # Minutos entre checks
ENABLED_LEAGUES=262,39,140  # IDs de ligas (Liga MX, EPL, La Liga)

# Railway
RAILWAY_ENVIRONMENT=production
PORT=8000
```

### 3. Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/football-betting-bot.git
cd football-betting-bot

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
python scripts/setup_database.py

# Ejecutar bot
python main.py
```

---

## 🚂 Deployment en Railway

### Paso 1: Preparar Proyecto

```bash
# Asegurar archivos necesarios
.
├── main.py
├── requirements.txt
├── Procfile
├── runtime.txt
└── railway.json
```

**Procfile:**
```
worker: python main.py
```

**runtime.txt:**
```
python-3.11.7
```

**railway.json:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Paso 2: Deploy en Railway

1. **Crear cuenta**: https://railway.app
2. **New Project** → Deploy from GitHub
3. **Add PostgreSQL** database
4. **Configurar variables de entorno** (ver sección Variables)
5. **Deploy automático** al hacer push a main

### Paso 3: Configurar PostgreSQL

Railway auto-provisiona PostgreSQL y genera `DATABASE_URL`. No requiere configuración manual.

### Paso 4: Monitoreo

```bash
# Ver logs en tiempo real
railway logs

# Status del servicio
railway status

# Variables de entorno
railway variables
```

---

## 🗄️ Variables de Entorno

### Obligatorias

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `RAPIDAPI_KEY` | API key de RapidAPI para API-Football | `abc123xyz...` |
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram | `123456:ABC-DEF...` |
| `TELEGRAM_CHAT_ID` | ID del chat donde enviar alertas | `-1001234567890` |
| `DATABASE_URL` | URL de PostgreSQL (Railway auto-genera) | `postgresql://...` |

### Opcionales

| Variable | Descripción | Default |
|----------|-------------|---------|
| `ALERT_TIME_MINUTES` | Minutos antes del partido para alertar | `60` |
| `MINIMUM_EDGE` | Edge mínimo para considerar value bet | `0.05` (5%) |
| `CHECK_INTERVAL` | Minutos entre cada check de partidos | `30` |
| `ENABLED_LEAGUES` | IDs de ligas separados por coma | `262` (Liga MX) |
| `MIN_CONFIDENCE` | Confianza mínima (1-5) para alertar | `3` |
| `MAX_ALERTS_PER_DAY` | Límite de notificaciones diarias | `10` |

---

## 📁 Estructura del Proyecto

```
football-betting-bot/
│
├── main.py                      # Punto de entrada principal
├── requirements.txt             # Dependencias Python
├── Procfile                     # Config Railway
├── runtime.txt                  # Versión Python
├── railway.json                 # Config Railway
├── .env.example                 # Template de variables
├── .gitignore
├── README.md
│
├── src/
│   ├── __init__.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── api_football.py      # Cliente API-Football
│   │   └── rate_limiter.py      # Control de rate limits
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── connection.py        # DB connection pool
│   │   └── migrations/          # SQL migrations
│   │
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── poisson_analyzer.py  # Distribución Poisson
│   │   ├── form_analyzer.py     # Análisis de racha
│   │   ├── h2h_analyzer.py      # Head-to-head
│   │   └── value_detector.py    # Detector de value bets
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── data_collector.py    # Recolección de datos
│   │   ├── scheduler.py         # Tareas programadas
│   │   └── cache_manager.py     # Cache en memoria
│   │
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── telegram_bot.py      # Bot de Telegram
│   │   └── message_formatter.py # Formateo de mensajes
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py             # Carga de configuración
│       ├── logger.py             # Logging centralizado
│       └── validators.py         # Validaciones
│
├── scripts/
│   ├── setup_database.py        # Inicializar BD
│   ├── seed_leagues.py          # Poblar ligas
│   └── test_notifications.py    # Test bot Telegram
│
├── tests/
│   ├── __init__.py
│   ├── test_analyzers.py
│   ├── test_api.py
│   └── test_value_detector.py
│
└── docs/
    ├── API_FOOTBALL.md          # Documentación de la API
    ├── STATISTICAL_METHODS.md   # Métodos estadísticos
    ├── DEPLOYMENT.md            # Guía de deployment
    └── EXAMPLES.md              # Ejemplos de uso
```

---

## 📊 Schema de Base de Datos

```sql
-- Ligas configuradas
CREATE TABLE leagues (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    country VARCHAR(50),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Equipos
CREATE TABLE teams (
    id INTEGER PRIMARY KEY,
    league_id INTEGER REFERENCES leagues(id),
    name VARCHAR(100),
    logo_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Partidos
CREATE TABLE fixtures (
    id INTEGER PRIMARY KEY,
    league_id INTEGER REFERENCES leagues(id),
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    kickoff_time TIMESTAMP,
    status VARCHAR(20),
    venue VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Estadísticas de equipos
CREATE TABLE team_statistics (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    league_id INTEGER REFERENCES leagues(id),
    season INTEGER,
    matches_played INTEGER,
    wins INTEGER,
    draws INTEGER,
    losses INTEGER,
    goals_scored INTEGER,
    goals_conceded INTEGER,
    home_wins INTEGER,
    home_goals_scored INTEGER,
    away_wins INTEGER,
    away_goals_scored INTEGER,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Histórico de cuotas
CREATE TABLE odds_history (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER REFERENCES fixtures(id),
    bookmaker VARCHAR(50),
    market_type VARCHAR(20), -- '1X2', 'Over/Under', etc.
    outcome VARCHAR(20),     -- 'Home', 'Draw', 'Away', 'Over 2.5', etc.
    odds DECIMAL(5,2),
    scraped_at TIMESTAMP DEFAULT NOW()
);

-- Predicciones generadas
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER REFERENCES fixtures(id),
    home_probability DECIMAL(5,2),
    draw_probability DECIMAL(5,2),
    away_probability DECIMAL(5,2),
    expected_goals_home DECIMAL(4,2),
    expected_goals_away DECIMAL(4,2),
    confidence_score INTEGER, -- 1-5
    created_at TIMESTAMP DEFAULT NOW()
);

-- Value bets detectadas
CREATE TABLE value_bets (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER REFERENCES fixtures(id),
    prediction_id INTEGER REFERENCES predictions(id),
    recommended_outcome VARCHAR(20),
    calculated_probability DECIMAL(5,2),
    bookmaker_odds DECIMAL(5,2),
    edge DECIMAL(5,2),
    expected_value DECIMAL(5,2),
    suggested_stake DECIMAL(5,2), -- % del bankroll
    created_at TIMESTAMP DEFAULT NOW()
);

-- Log de notificaciones
CREATE TABLE notifications_log (
    id SERIAL PRIMARY KEY,
    value_bet_id INTEGER REFERENCES value_bets(id),
    telegram_message_id BIGINT,
    sent_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) -- 'sent', 'failed', 'retry'
);

-- Índices para performance
CREATE INDEX idx_fixtures_kickoff ON fixtures(kickoff_time);
CREATE INDEX idx_fixtures_league ON fixtures(league_id);
CREATE INDEX idx_odds_fixture ON odds_history(fixture_id);
CREATE INDEX idx_predictions_fixture ON predictions(fixture_id);
CREATE INDEX idx_value_bets_fixture ON value_bets(fixture_id);
```

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Tests específicos
pytest tests/test_analyzers.py
pytest tests/test_value_detector.py

# Con coverage
pytest --cov=src tests/

# Test de integración con Telegram
python scripts/test_notifications.py
```

---

## 📈 Roadmap

### Fase 1 - MVP (Semana 1-2)
- [x] Documentación completa
- [ ] Estructura del proyecto
- [ ] Integración API-Football
- [ ] Base de datos PostgreSQL
- [ ] Bot de Telegram básico
- [ ] Deploy en Railway

### Fase 2 - Análisis Estadístico (Semana 3-4)
- [ ] Implementar Poisson analyzer
- [ ] Form analyzer (racha)
- [ ] Head-to-head analyzer
- [ ] Value bet detector
- [ ] Sistema de alertas

### Fase 3 - Optimización (Semana 5-6)
- [ ] Cache de datos
- [ ] Rate limiting inteligente
- [ ] Backtesting con datos históricos
- [ ] Dashboard web (opcional)
- [ ] Múltiples ligas

### Fase 4 - Producción (Semana 7-8)
- [ ] Monitoring y alertas
- [ ] Auto-scaling en Railway
- [ ] Documentación completa
- [ ] Tests automatizados
- [ ] CI/CD pipeline

---

## ⚠️ Disclaimer

Este bot es una herramienta de análisis estadístico con fines educativos y de investigación.

**IMPORTANTE:**
- No garantiza ganancias
- Las apuestas conllevan riesgo de pérdida
- Apostar solo lo que puedas permitirte perder
- Verifica las leyes locales sobre apuestas
- Juego responsable siempre

---

## 📝 Licencia

MIT License - Ver archivo `LICENSE` para detalles

---

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📧 Contacto

Para preguntas o sugerencias, abre un issue en GitHub.

---

**Construido con 📊 análisis estadístico puro - No IA, solo matemáticas reales**
