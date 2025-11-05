# 🎯 Guía Completa de Integración: FootyStats API

## 📋 Resumen Ejecutivo

Esta guía documenta la integración completa de **FootyStats API** al bot de predicciones de fútbol, con enfoque especial en **estadísticas de córners** y datos adicionales que complementan API-Football.

---

## 🎯 Objetivos de la Integración

### ¿Por qué FootyStats?

1. **✅ Especialización en Córners**: Datos detallados de córners que API-Football no ofrece
2. **✅ Estadísticas de Apuestas**: BTTS, Over/Under optimizados para betting
3. **✅ Predicciones de Córners**: Pre-match average corners y probabilidades
4. **✅ Datos Complementarios**: 710+ data points por equipo
5. **✅ Costo-Beneficio**: Planes desde £29.99/mes (más económico para datos específicos)

### Casos de Uso Principales

```
1. Predicciones de Córners
   → Detectar value bets en mercados de córners (Over/Under X.5)

2. Análisis Avanzado
   → Combinar datos de ambas APIs para predicciones más precisas

3. Estrategias Específicas
   → Córners + goles para detección de patrones

4. Diversificación
   → Reducir dependencia de una sola API
```

---

## 📊 Análisis Comparativo: FootyStats vs API-Football

### Tabla de Comparación Detallada

| Característica | API-Football | FootyStats | Recomendación |
|----------------|--------------|------------|---------------|
| **Cobertura** | 950+ ligas | 1500+ ligas | 🟢 FootyStats |
| **Actualización Live** | 15 segundos | 20 minutos | 🟢 API-Football |
| **Córners Detallados** | ❌ Básico | ✅ Avanzado | 🟢 FootyStats |
| **Predicciones Built-in** | ✅ Básicas | ✅ Betting-focused | 🟡 Empate |
| **Rate Limit** | 250 req/min | 60-90 req/min | 🟢 API-Football |
| **Costo Mensual** | Variable | £29.99-£389.99 | 🟡 Depende |
| **Formato** | JSON | JSON | 🟡 Ambos iguales |
| **Autenticación** | Header | URL param | 🟡 Preferencia |
| **Datos Históricos** | ✅ Extenso | ✅ Extenso | 🟡 Ambos buenos |
| **Odds en Vivo** | ✅ Sí | ❌ Pre-match | 🟢 API-Football |

### Conclusión del Análisis

**🎯 ESTRATEGIA RECOMENDADA: Uso Complementario**

```
API-Football (Principal)
├─ Live scores y updates
├─ Fixtures y eventos en tiempo real
├─ Odds en vivo
└─ Predicciones generales

FootyStats (Complementario)
├─ Estadísticas de córners
├─ Análisis BTTS detallado
├─ Pre-match predictions especializadas
└─ Datos históricos avanzados
```

---

## 🔑 Capacidades de FootyStats API

### 📡 Endpoints Principales

#### 1. **Match Schedule & Stats**

```http
GET https://api.football-data-api.com/league-matches?key=YOUR_KEY&season_id=2012
```

**Datos Incluidos**:
```json
{
  "id": 453873,
  "homeID": 149,
  "awayID": 108,
  "date_unix": 1577836800,
  "competition_id": 2,
  "season": "2018/2019",
  "status": "complete",
  "game_week": 1,
  "homeGoalCount": 2,
  "awayGoalCount": 1,
  "totalGoalCount": 3,

  // CÓRNERS (clave para nosotros)
  "team_a_corners": 2,
  "team_b_corners": 7,
  "pre_match_average_corners": 10.5,
  "pre_match_corners_over85": 65,
  "pre_match_corners_over95": 52,
  "pre_match_corners_over105": 38,
  "pre_match_corners_over115": 25,

  // BTTS
  "pre_match_teamA_btts_percentage": 75,
  "pre_match_teamB_btts_percentage": 68,

  // Otros
  "attendance": 59936,
  "odds_ft_1": 1.75,
  "odds_ft_x": 3.80,
  "odds_ft_2": 5.20
}
```

#### 2. **Team Statistics**

```http
GET https://api.football-data-api.com/team?key=YOUR_KEY&team_id=149
```

**Datos Incluidos** (710+ data points):
```json
{
  "id": 149,
  "name": "Manchester City",
  "cleanName": "Manchester City",
  "country": "England",

  // Estadísticas de córners
  "avg_corners_overall": 6.2,
  "avg_corners_home": 6.8,
  "avg_corners_away": 5.6,
  "corners_total": 124,
  "corners_for": 80,
  "corners_against": 44,

  // Promedios Over/Under
  "corner_stats": {
    "total_over_85": 15,
    "total_under_85": 5,
    "percentage_over_85": 75
  }
}
```

#### 3. **League Corner Stats**

```http
GET https://api.football-data-api.com/league-season?key=YOUR_KEY&season_id=2012
```

**Promedios de Liga**:
```json
{
  "season_id": 2012,
  "name": "Premier League 2024/2025",
  "avg_corners_per_match": 10.5,
  "avg_corners_first_half": 4.8,
  "avg_corners_second_half": 5.7,
  "total_matches": 380
}
```

### 📊 Data Points Clave para Córners

| Data Point | Descripción | Utilidad |
|------------|-------------|----------|
| `team_a_corners` | Córners del equipo local | Estadística real del partido |
| `team_b_corners` | Córners del equipo visitante | Estadística real del partido |
| `pre_match_average_corners` | Promedio esperado | Predicción pre-partido |
| `pre_match_corners_over85` | % probabilidad Over 8.5 | Value bet detection |
| `pre_match_corners_over95` | % probabilidad Over 9.5 | Value bet detection |
| `pre_match_corners_over105` | % probabilidad Over 10.5 | Value bet detection |
| `pre_match_corners_over115` | % probabilidad Over 11.5 | Value bet detection |
| `avg_corners_overall` | Promedio del equipo | Análisis de forma |
| `avg_corners_home/away` | Promedios por localía | Factor home/away |

---

## 💰 Análisis de Costos y Límites

### 📋 Planes Disponibles

| Plan | Precio | Ligas | Requests/Hour | Requests/Min | Recomendado Para |
|------|--------|-------|---------------|--------------|------------------|
| **Hobby** | £29.99/mes | 40 | 1,800 | 60 | Testing, desarrollo |
| **Serious** | £69.99/mes | 150 | 3,600 | 90 | Producción básica |
| **Everything** | £389.99/mes | 1,500+ | 4,500 | 90 | Producción completa |

### 💵 Recomendación de Plan

**Para nuestro caso: Plan HOBBY (£29.99/mes)**

**Razones**:
1. ✅ Monitoreamos ~5-10 ligas principales (suficiente con 40)
2. ✅ Uso complementario (no reemplaza API-Football)
3. ✅ 1,800 req/hour es suficiente para:
   - Pre-match analysis: ~50 calls/día
   - Historical data: ~100 calls/día
   - Buffer: 1,650 calls disponibles
4. ✅ Costo bajo para datos de valor alto

### 📊 Estimación de Uso Diario

```
Escenario: 10 partidos analizados por día

Pre-Match Analysis:
- 10 partidos × 1 call (match data) = 10 calls
- 10 partidos × 2 calls (team stats) = 20 calls
- 1 call (league stats) × 5 ligas = 5 calls
TOTAL PRE-MATCH: 35 calls/día

Historical Data (opcional):
- Análisis de tendencias: ~20 calls/día

TOTAL DIARIO: ~55 calls
TOTAL MENSUAL: ~1,650 calls
LÍMITE MENSUAL (Hobby): ~54,000 calls

MARGEN: 97% disponible ✅
```

### ⚠️ Rate Limiting

```python
# FootyStats: 60-90 req/min
# API-Football: 250 req/min

# Estrategia:
# - API-Football: Tiempo real y live
# - FootyStats: Pre-match y análisis histórico
# - No hay conflicto de límites
```

---

## 🏗️ Arquitectura de Integración

### 🎨 Diseño Propuesto

```
┌─────────────────────────────────────────────────────────────┐
│                    PREDICTION BOT SYSTEM                     │
└─────────────────────────────────────────────────────────────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
        ┌────────▼────────┐       ┌───────▼──────┐
        │  API-Football   │       │  FootyStats  │
        │   (Primary)     │       │ (Secondary)  │
        └────────┬────────┘       └───────┬──────┘
                 │                         │
                 │    ┌────────────────────┘
                 │    │
        ┌────────▼────▼─────┐
        │   API Manager      │
        │  (Orchestrator)    │
        └────────┬───────────┘
                 │
        ┌────────▼───────────┐
        │  Unified Analyzer  │
        │  (Combina datos)   │
        └────────┬───────────┘
                 │
        ┌────────▼───────────┐
        │  Corner Predictor  │ ← NUEVO
        │   (Especializado)  │
        └────────────────────┘
```

### 🔧 Componentes Nuevos a Desarrollar

#### 1. **FootyStatsClient** (Nuevo)

```python
# src/api/footystats_client.py

class FootyStatsClient:
    """Cliente para FootyStats API"""

    BASE_URL = "https://api.football-data-api.com"

    def __init__(self):
        self.api_key = Config.FOOTYSTATS_API_KEY
        self.rate_limiter = RateLimiter(
            max_requests=60,  # 60 req/min
            time_window=60
        )

    def get_match_stats(self, match_id: int) -> Dict:
        """Obtiene estadísticas completas de un partido"""

    def get_team_stats(self, team_id: int) -> Dict:
        """Obtiene estadísticas de un equipo"""

    def get_corner_stats(self, match_id: int) -> Dict:
        """Obtiene estadísticas específicas de córners"""

    def get_league_averages(self, season_id: int) -> Dict:
        """Obtiene promedios de la liga"""
```

#### 2. **APIManager** (Orquestador)

```python
# src/api/api_manager.py

class APIManager:
    """
    Gestiona múltiples fuentes de API
    Decide cuál API usar para cada tipo de dato
    """

    def __init__(self):
        self.api_football = APIFootballClient()
        self.footystats = FootyStatsClient()

    def get_fixture_data(self, fixture_id: int) -> Dict:
        """
        Combina datos de ambas APIs
        - API-Football: Estado del partido, odds, eventos
        - FootyStats: Córners, BTTS, estadísticas avanzadas
        """

    def get_comprehensive_team_stats(self, team_id: int) -> Dict:
        """Combina estadísticas de ambas APIs"""
```

#### 3. **CornerAnalyzer** (Analizador Especializado)

```python
# src/analyzers/corner_analyzer.py

class CornerAnalyzer:
    """
    Analiza estadísticas de córners y detecta value bets
    """

    def calculate_expected_corners(
        self,
        home_avg: float,
        away_avg: float,
        league_avg: float
    ) -> Tuple[float, float]:
        """Calcula córners esperados por equipo"""

    def calculate_total_corners_probability(
        self,
        expected_total: float,
        thresholds: List[float] = [8.5, 9.5, 10.5, 11.5]
    ) -> Dict[float, float]:
        """
        Calcula probabilidades para Over/Under córners
        Retorna: {8.5: 0.75, 9.5: 0.60, ...}
        """

    def detect_corner_value_bets(
        self,
        probabilities: Dict,
        market_odds: Dict
    ) -> List[Dict]:
        """Detecta value bets en mercado de córners"""
```

#### 4. **CornerStatistics** (Modelo de BD)

```python
# src/database/models.py

class CornerStatistics(Base):
    """Estadísticas de córners por partido"""

    __tablename__ = "corner_statistics"

    id = Column(Integer, primary_key=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"))

    # Córners reales
    home_corners = Column(Integer)
    away_corners = Column(Integer)
    total_corners = Column(Integer)

    # Córners por tiempo
    first_half_corners = Column(Integer)
    second_half_corners = Column(Integer)

    # Predicciones pre-match (de FootyStats)
    pre_match_avg_corners = Column(Float)
    pre_match_over_85_prob = Column(Float)
    pre_match_over_95_prob = Column(Float)
    pre_match_over_105_prob = Column(Float)
    pre_match_over_115_prob = Column(Float)

    # Promedios de equipos
    home_team_avg_corners = Column(Float)
    away_team_avg_corners = Column(Float)

    # Análisis
    expected_total_corners = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)
```

#### 5. **CornerValueBet** (Modelo de BD)

```python
class CornerValueBet(Base):
    """Value bets detectados en mercado de córners"""

    __tablename__ = "corner_value_bets"

    id = Column(Integer, primary_key=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"))
    corner_stat_id = Column(Integer, ForeignKey("corner_statistics.id"))

    # Mercado
    market_type = Column(String)  # "over_85", "over_95", etc.
    threshold = Column(Float)  # 8.5, 9.5, 10.5, 11.5

    # Análisis
    calculated_probability = Column(Float)
    bookmaker_odds = Column(Float)
    implied_probability = Column(Float)
    edge = Column(Float)

    # Recomendación
    is_value_bet = Column(Boolean, default=False)
    confidence = Column(String)  # "low", "medium", "high"
    suggested_stake = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 📅 Plan de Implementación Fase a Fase

### 🎯 Fase 1: Foundation & Setup (Semana 1)

**Objetivos**:
- ✅ Configurar cuenta FootyStats
- ✅ Crear cliente básico
- ✅ Tests de conectividad

**Tareas Detalladas**:

```bash
1.1 Configuración Inicial
────────────────────────
□ Crear cuenta en FootyStats.org
□ Suscribirse al plan Hobby (£29.99/mes)
□ Obtener API Key
□ Documentar credenciales en .env.example

1.2 Estructura de Archivos
──────────────────────────
□ Crear src/api/footystats_client.py
□ Crear src/analyzers/corner_analyzer.py
□ Crear tests/test_footystats_client.py

1.3 Cliente Básico
─────────────────
□ Implementar FootyStatsClient.__init__
□ Implementar rate limiter (60 req/min)
□ Implementar _make_request con retry logic
□ Implementar manejo de errores

1.4 Tests de Conectividad
────────────────────────
□ Test de autenticación
□ Test de rate limiting
□ Test de manejo de errores
□ Test con API key=example

1.5 Configuración
────────────────
□ Agregar FOOTYSTATS_API_KEY a Config
□ Agregar FOOTYSTATS_ENABLED (on/off)
□ Documentar en DEVELOPMENT.md
```

**Entregables**:
- ✅ FootyStatsClient funcional
- ✅ Tests pasando
- ✅ Documentación actualizada

**Tiempo Estimado**: 3-5 días

---

### 🎯 Fase 2: Core Endpoints (Semana 2)

**Objetivos**:
- ✅ Implementar endpoints principales
- ✅ Parsear respuestas JSON
- ✅ Cachear datos apropiadamente

**Tareas Detalladas**:

```bash
2.1 Endpoint: Match Statistics
──────────────────────────────
□ Implementar get_match_stats(match_id)
□ Parsear respuesta JSON
□ Extraer córners y BTTS
□ Manejar casos edge (partido sin datos)
□ Tests unitarios

2.2 Endpoint: Team Statistics
─────────────────────────────
□ Implementar get_team_stats(team_id)
□ Extraer promedios de córners
□ Extraer tendencias BTTS
□ Cache de 24 horas (datos estables)
□ Tests unitarios

2.3 Endpoint: League Averages
─────────────────────────────
□ Implementar get_league_season(season_id)
□ Extraer promedios de liga
□ Cache de 1 semana (datos muy estables)
□ Tests unitarios

2.4 Sistema de Cache
───────────────────
□ Crear FootyStatsCache (similar a fixtures_cache)
□ TTL diferenciados:
  - Match stats: 1 hora
  - Team stats: 24 horas
  - League stats: 7 días
□ Tests de invalidación

2.5 ID Mapping
─────────────
□ Crear tabla team_id_mappings (API-Football ↔ FootyStats)
□ Crear función map_team_ids()
□ Poblar mappings de ligas principales
□ Documentar proceso de mapping
```

**Entregables**:
- ✅ 3 endpoints funcionales
- ✅ Sistema de cache robusto
- ✅ Mapping de IDs documentado

**Tiempo Estimado**: 5-7 días

---

### 🎯 Fase 3: Corner Analyzer (Semana 3)

**Objetivos**:
- ✅ Algoritmo de predicción de córners
- ✅ Detección de value bets
- ✅ Integración con sistema actual

**Tareas Detalladas**:

```bash
3.1 Modelos de Base de Datos
────────────────────────────
□ Crear modelo CornerStatistics
□ Crear modelo CornerValueBet
□ Crear migración de BD
□ Ejecutar migración en dev
□ Tests de modelos

3.2 CornerAnalyzer: Algoritmo Core
──────────────────────────────────
□ Implementar calculate_expected_corners()
  - Usar promedios de equipos
  - Ajustar por home/away
  - Considerar promedio de liga

□ Implementar calculate_total_corners_probability()
  - Usar distribución de Poisson
  - Calcular Over/Under 8.5, 9.5, 10.5, 11.5

□ Implementar calculate_corner_ranges()
  - Similar a goal_ranges
  - Rangos: 0-7, 8-10, 11-13, 14+

□ Tests unitarios exhaustivos

3.3 Value Bet Detection
──────────────────────
□ Implementar detect_corner_value_bets()
□ Comparar probabilidades calculadas vs odds
□ Calcular edge
□ Aplicar umbral mínimo (Config.MINIMUM_EDGE_CORNERS)
□ Tests con datos reales

3.4 Integración con BotService
──────────────────────────────
□ Agregar corner_analyzer a BotService
□ Llamar a FootyStats en _analyze_and_notify()
□ Guardar CornerStatistics en BD
□ Detectar CornerValueBets
□ Tests de integración
```

**Entregables**:
- ✅ CornerAnalyzer completo
- ✅ Modelos de BD migrados
- ✅ Integración funcional

**Tiempo Estimado**: 5-7 días

---

### 🎯 Fase 4: User Interface (Semana 4)

**Objetivos**:
- ✅ Notificaciones de córners
- ✅ Comandos Telegram
- ✅ Formateo de mensajes

**Tareas Detalladas**:

```bash
4.1 Message Formatter
────────────────────
□ Crear format_corner_analysis()
□ Crear format_corner_value_bet()
□ Incluir emojis apropiados
□ Formato claro y conciso
□ Tests de formato

4.2 Notificaciones
─────────────────
□ send_corner_value_bet_alert()
□ Incluir análisis de córners en alertas principales
□ Configuración on/off por usuario
□ Tests de envío

4.3 Comandos Telegram
────────────────────
□ /corners_stats <fixture_id>
  - Mostrar análisis de córners
  - Promedios de equipos
  - Predicción de total

□ /corner_trends <team_id>
  - Tendencias históricas
  - Promedios home/away
  - Gráfico de texto

□ Actualizar /analizar para incluir córners
□ Tests de comandos

4.4 Menú Interactivo
───────────────────
□ Agregar opción "📊 Córners" al menú
□ Sub-menú con análisis
□ Callback handlers
□ Tests de navegación
```

**Entregables**:
- ✅ Sistema de notificaciones completo
- ✅ Comandos funcionando
- ✅ UI intuitiva

**Tiempo Estimado**: 5-7 días

---

### 🎯 Fase 5: Optimization & Polish (Semana 5)

**Objetivos**:
- ✅ Optimizar performance
- ✅ Documentación completa
- ✅ Monitoreo y métricas

**Tareas Detalladas**:

```bash
5.1 Performance
──────────────
□ Optimizar queries de BD
□ Índices apropiados
□ Batch processing cuando posible
□ Profiling y benchmarks

5.2 Error Handling
─────────────────
□ Manejo robusto de errores FootyStats
□ Fallbacks si API no disponible
□ Logs detallados
□ Alertas de errores críticos

5.3 Configuración Avanzada
─────────────────────────
□ Config.CORNER_ANALYSIS_ENABLED
□ Config.MINIMUM_EDGE_CORNERS
□ Config.CORNER_THRESHOLDS = [8.5, 9.5, 10.5, 11.5]
□ Config.FOOTYSTATS_CACHE_TTL
□ Validaciones Pydantic

5.4 Documentación
────────────────
□ Actualizar README.md
□ Crear FOOTYSTATS_GUIDE.md (usuario final)
□ Documentar todos los endpoints
□ Ejemplos de uso
□ Troubleshooting guide

5.5 Monitoring
─────────────
□ Métricas de uso de FootyStats
□ Tasa de acierto de predicciones de córners
□ Value bets de córners detectados
□ ROI de estrategia de córners
□ Dashboard (opcional)

5.6 Testing Final
────────────────
□ Tests end-to-end
□ Tests de carga
□ Tests con datos reales de producción
□ Validación de QA
```

**Entregables**:
- ✅ Sistema optimizado
- ✅ Documentación completa
- ✅ Métricas funcionando

**Tiempo Estimado**: 5-7 días

---

### 🎯 Fase 6: Advanced Features (Futuro - Opcional)

**Features Avanzadas**:

```bash
6.1 Machine Learning para Córners
─────────────────────────────────
□ Entrenar modelo con datos históricos
□ Predecir córners con ML
□ Comparar vs Poisson
□ A/B testing

6.2 Live Corner Updates
──────────────────────
□ Monitoreo de córners en vivo
□ Actualizar probabilidades durante el partido
□ Notificaciones de tendencias
□ "Live corner momentum"

6.3 Combined Strategies
──────────────────────
□ Córners + goles (correlaciones)
□ Córners + tarjetas
□ Estrategias combinadas
□ Detección de patrones

6.4 Dashboard Web
────────────────
□ Visualización de estadísticas de córners
□ Gráficos históricos
□ Comparación de equipos
□ Exportar reportes
```

**Tiempo Estimado**: Variable (según prioridades)

---

## 💻 Ejemplos de Código Detallados

### 1. FootyStatsClient Completo

```python
"""
FootyStats API Client
Handles all interactions with FootyStats API
"""
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .rate_limiter import RateLimiter
from ..utils.config import Config
from ..utils.logger import setup_logger
from ..utils.cache import SimpleCache

logger = setup_logger(__name__)


class FootyStatsClient:
    """
    Cliente para FootyStats API

    Documentación: https://footystats.org/api/documentations/
    """

    BASE_URL = "https://api.football-data-api.com"

    def __init__(self):
        """Inicializa el cliente"""
        if not Config.FOOTYSTATS_API_KEY:
            raise ValueError("FOOTYSTATS_API_KEY not configured")

        self.api_key = Config.FOOTYSTATS_API_KEY

        # Rate limiter: 60 requests per minute (plan Hobby)
        self.rate_limiter = RateLimiter(max_requests=60, time_window=60)

        # Cache dedicado
        self.cache = SimpleCache()

        logger.info("FootyStats client initialized")

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        cache_ttl: int = 3600
    ) -> Dict[str, Any]:
        """
        Make HTTP request to FootyStats API

        Args:
            endpoint: API endpoint (sin base URL)
            params: Query parameters adicionales
            cache_ttl: TTL del cache en segundos

        Returns:
            Response JSON data

        Raises:
            requests.RequestException: On request failure
        """
        # Preparar parámetros
        if params is None:
            params = {}

        # IMPORTANTE: FootyStats usa query parameter para auth
        params["key"] = self.api_key

        # Construir cache key
        cache_key = f"footystats:{endpoint}:{str(params)}"

        # Verificar cache
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for {endpoint}")
            return cached_data

        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            logger.debug(f"Making request to FootyStats: {endpoint}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Guardar en cache
            self.cache.set(cache_key, data, ttl_seconds=cache_ttl)

            logger.debug(f"FootyStats request successful: {endpoint}")
            return data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.error("FootyStats rate limit exceeded")
                raise Exception("Rate limit exceeded") from e
            elif e.response.status_code == 401:
                logger.error("FootyStats authentication failed - check API key")
                raise Exception("Authentication failed") from e
            else:
                logger.error(f"FootyStats HTTP error: {e}")
                raise

        except requests.exceptions.RequestException as e:
            logger.error(f"FootyStats request failed: {e}")
            raise

    def get_match_stats(self, match_id: int) -> Optional[Dict]:
        """
        Obtiene estadísticas completas de un partido

        Args:
            match_id: FootyStats match ID

        Returns:
            Match statistics including corners, BTTS, etc.
        """
        logger.info(f"Fetching match stats for match {match_id}")

        try:
            # Endpoint para match específico
            # Nota: FootyStats no tiene endpoint directo por match_id
            # Necesitamos usar league-matches y filtrar
            # O usar un mapping previo

            # Por ahora, retornamos estructura de ejemplo
            # En implementación real, usar endpoint apropiado

            data = self._make_request(
                "league-matches",
                params={"match_id": match_id},
                cache_ttl=3600  # 1 hora
            )

            return data.get("data", {})

        except Exception as e:
            logger.error(f"Error fetching match stats: {e}")
            return None

    def get_team_stats(self, team_id: int, season_id: Optional[int] = None) -> Optional[Dict]:
        """
        Obtiene estadísticas de un equipo

        Args:
            team_id: FootyStats team ID
            season_id: Optional season ID

        Returns:
            Team statistics including corner averages
        """
        logger.info(f"Fetching team stats for team {team_id}")

        try:
            params = {"team_id": team_id}
            if season_id:
                params["season_id"] = season_id

            data = self._make_request(
                "team",
                params=params,
                cache_ttl=86400  # 24 horas (datos estables)
            )

            return data.get("data", {})

        except Exception as e:
            logger.error(f"Error fetching team stats: {e}")
            return None

    def get_league_season(self, season_id: int) -> Optional[Dict]:
        """
        Obtiene promedios y estadísticas de una temporada de liga

        Args:
            season_id: FootyStats season ID

        Returns:
            League season statistics
        """
        logger.info(f"Fetching league season stats for season {season_id}")

        try:
            data = self._make_request(
                "league-season",
                params={"season_id": season_id},
                cache_ttl=604800  # 7 días (muy estable)
            )

            return data.get("data", {})

        except Exception as e:
            logger.error(f"Error fetching league season: {e}")
            return None

    def get_corner_stats(self, match_id: int) -> Optional[Dict]:
        """
        Extrae específicamente estadísticas de córners de un partido

        Args:
            match_id: FootyStats match ID

        Returns:
            Dictionary con estadísticas de córners
        """
        match_data = self.get_match_stats(match_id)

        if not match_data:
            return None

        return {
            "team_a_corners": match_data.get("team_a_corners", 0),
            "team_b_corners": match_data.get("team_b_corners", 0),
            "total_corners": match_data.get("team_a_corners", 0) + match_data.get("team_b_corners", 0),
            "pre_match_average_corners": match_data.get("pre_match_average_corners", 0),
            "pre_match_over_85": match_data.get("pre_match_corners_over85", 0),
            "pre_match_over_95": match_data.get("pre_match_corners_over95", 0),
            "pre_match_over_105": match_data.get("pre_match_corners_over105", 0),
            "pre_match_over_115": match_data.get("pre_match_corners_over115", 0)
        }

    def get_team_corner_stats(self, team_id: int) -> Optional[Dict]:
        """
        Extrae estadísticas de córners de un equipo

        Args:
            team_id: FootyStats team ID

        Returns:
            Dictionary con promedios de córners del equipo
        """
        team_data = self.get_team_stats(team_id)

        if not team_data:
            return None

        return {
            "avg_corners_overall": team_data.get("avg_corners_overall", 0),
            "avg_corners_home": team_data.get("avg_corners_home", 0),
            "avg_corners_away": team_data.get("avg_corners_away", 0),
            "corners_total": team_data.get("corners_total", 0),
            "corners_for": team_data.get("corners_for", 0),
            "corners_against": team_data.get("corners_against", 0)
        }
```

### 2. CornerAnalyzer Completo

```python
"""
Corner statistics analyzer using Poisson distribution
"""
import numpy as np
from scipy.stats import poisson
from typing import Dict, Tuple, List
from math import floor

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class CornerAnalyzer:
    """
    Analiza estadísticas de córners y detecta value bets

    Usa distribución de Poisson similar al análisis de goles
    """

    # Umbrales estándar de mercado
    STANDARD_THRESHOLDS = [8.5, 9.5, 10.5, 11.5, 12.5]

    @staticmethod
    def calculate_expected_corners(
        home_team_avg: float,
        away_team_avg: float,
        league_avg: float = 10.5,
        home_advantage_factor: float = 1.1
    ) -> Tuple[float, float]:
        """
        Calcula córners esperados para cada equipo

        Similar al cálculo de goles esperados, pero adaptado para córners

        Args:
            home_team_avg: Promedio de córners del equipo local
            away_team_avg: Promedio de córners del equipo visitante
            league_avg: Promedio de córners de la liga
            home_advantage_factor: Factor de ventaja local (default 1.1 = +10%)

        Returns:
            Tuple de (expected_home_corners, expected_away_corners)
        """
        # Validar inputs
        if league_avg <= 0:
            logger.warning(f"Invalid league_avg: {league_avg}, using default 10.5")
            league_avg = 10.5

        # Calcular strength relativo a la liga
        home_strength = home_team_avg / league_avg
        away_strength = away_team_avg / league_avg

        # Aplicar home advantage
        home_strength *= home_advantage_factor

        # Calcular córners esperados
        # Asumimos que cada equipo contribuye independientemente
        expected_home = home_strength * (league_avg / 2)
        expected_away = away_strength * (league_avg / 2)

        logger.debug(
            f"Expected corners: Home={expected_home:.2f}, Away={expected_away:.2f}"
        )

        return round(expected_home, 2), round(expected_away, 2)

    @staticmethod
    def calculate_total_corners_probability(
        expected_home: float,
        expected_away: float,
        thresholds: List[float] = None
    ) -> Dict[float, Dict[str, float]]:
        """
        Calcula probabilidades de Over/Under para córners totales

        Args:
            expected_home: Córners esperados del local
            expected_away: Córners esperados del visitante
            thresholds: Lista de umbrales (default: [8.5, 9.5, 10.5, 11.5, 12.5])

        Returns:
            Dictionary: {
                8.5: {"over": 0.75, "under": 0.25},
                9.5: {"over": 0.65, "under": 0.35},
                ...
            }
        """
        if thresholds is None:
            thresholds = CornerAnalyzer.STANDARD_THRESHOLDS

        total_expected = expected_home + expected_away

        probabilities = {}

        for threshold in thresholds:
            # Usar Poisson CDF para calcular probabilidades
            # P(X <= threshold) = CDF(floor(threshold), lambda)
            under_prob = poisson.cdf(floor(threshold), total_expected)
            over_prob = 1 - under_prob

            probabilities[threshold] = {
                "over": round(over_prob, 4),
                "under": round(under_prob, 4)
            }

        logger.debug(
            f"Corner probabilities for total={total_expected:.2f}: "
            f"{probabilities}"
        )

        return probabilities

    @staticmethod
    def calculate_corner_ranges(
        expected_home: float,
        expected_away: float
    ) -> Dict[str, float]:
        """
        Calcula probabilidades para rangos de córners totales

        Similar a goal_ranges pero para córners

        Args:
            expected_home: Córners esperados del local
            expected_away: Córners esperados del visitante

        Returns:
            Dictionary con probabilidades de rangos:
            {
                "0-7": 0.15,    # Muy pocos córners
                "8-10": 0.40,   # Normal
                "11-13": 0.30,  # Muchos córners
                "14+": 0.15     # Muchísimos córners
            }
        """
        total_expected = expected_home + expected_away

        # Usar CDF para calcular rangos
        cdf_7 = poisson.cdf(7, total_expected)
        cdf_10 = poisson.cdf(10, total_expected)
        cdf_13 = poisson.cdf(13, total_expected)

        ranges = {
            "0-7": round(cdf_7, 4),
            "8-10": round(cdf_10 - cdf_7, 4),
            "11-13": round(cdf_13 - cdf_10, 4),
            "14+": round(1 - cdf_13, 4)
        }

        logger.debug(f"Corner ranges: {ranges}")

        return ranges

    @staticmethod
    def detect_corner_value_bets(
        probabilities: Dict[float, Dict[str, float]],
        market_odds: Dict[float, Dict[str, float]],
        minimum_edge: float = 0.05
    ) -> List[Dict]:
        """
        Detecta value bets en mercado de córners

        Args:
            probabilities: Probabilidades calculadas
            market_odds: Odds del mercado (mismo formato que probabilities)
            minimum_edge: Edge mínimo para considerar value bet

        Returns:
            Lista de value bets detectados:
            [
                {
                    "threshold": 9.5,
                    "market": "over",
                    "calculated_prob": 0.65,
                    "odds": 1.80,
                    "implied_prob": 0.5556,
                    "edge": 0.0944,
                    "is_value": True
                },
                ...
            ]
        """
        value_bets = []

        for threshold in probabilities.keys():
            if threshold not in market_odds:
                logger.debug(f"No market odds for threshold {threshold}")
                continue

            for market_type in ["over", "under"]:
                if market_type not in market_odds[threshold]:
                    continue

                calc_prob = probabilities[threshold][market_type]
                odds = market_odds[threshold][market_type]

                # Calcular implied probability de las odds
                implied_prob = 1 / odds if odds > 0 else 0

                # Calcular edge
                edge = calc_prob - implied_prob

                # Determinar si es value bet
                is_value = edge >= minimum_edge

                if is_value:
                    logger.info(
                        f"🎯 Corner value bet detected: "
                        f"{market_type.upper()} {threshold} @ {odds} "
                        f"(edge: {edge*100:.1f}%)"
                    )

                value_bets.append({
                    "threshold": threshold,
                    "market": market_type,
                    "calculated_prob": calc_prob,
                    "odds": odds,
                    "implied_prob": implied_prob,
                    "edge": round(edge, 4),
                    "is_value": is_value,
                    "confidence": CornerAnalyzer._get_confidence_rating(edge)
                })

        # Ordenar por edge (mayor primero)
        value_bets.sort(key=lambda x: x["edge"], reverse=True)

        return value_bets

    @staticmethod
    def _get_confidence_rating(edge: float) -> str:
        """
        Determina rating de confianza basado en edge

        Args:
            edge: Edge calculado

        Returns:
            "low", "medium", o "high"
        """
        if edge >= 0.15:  # 15%+
            return "high"
        elif edge >= 0.10:  # 10-15%
            return "medium"
        else:  # 5-10%
            return "low"
```

---

## 🗃️ Migración de Base de Datos

### Script de Migración

```python
"""
Migration: Add corner statistics tables
"""
from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from src.database import db_manager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

Base = declarative_base()


def run_migration():
    """
    Crea las nuevas tablas para estadísticas de córners
    """
    logger.info("=" * 60)
    logger.info("Running Corner Statistics Migration")
    logger.info("=" * 60)

    engine = db_manager.get_engine()

    # Importar modelos para que SQLAlchemy los conozca
    from src.database.models import CornerStatistics, CornerValueBet, TeamIDMapping

    # Crear tablas
    logger.info("Creating corner_statistics table...")
    CornerStatistics.__table__.create(engine, checkfirst=True)
    logger.info("✅ corner_statistics table created")

    logger.info("Creating corner_value_bets table...")
    CornerValueBet.__table__.create(engine, checkfirst=True)
    logger.info("✅ corner_value_bets table created")

    logger.info("Creating team_id_mappings table...")
    TeamIDMapping.__table__.create(engine, checkfirst=True)
    logger.info("✅ team_id_mappings table created")

    logger.info("=" * 60)
    logger.info("✅ Migration completed successfully")
    logger.info("=" * 60)


def rollback_migration():
    """
    Elimina las tablas de córners (usar con cuidado)
    """
    logger.warning("=" * 60)
    logger.warning("⚠️  Rolling back Corner Statistics Migration")
    logger.warning("=" * 60)

    engine = db_manager.get_engine()

    from src.database.models import CornerStatistics, CornerValueBet, TeamIDMapping

    # Eliminar tablas en orden inverso (por foreign keys)
    logger.info("Dropping corner_value_bets table...")
    CornerValueBet.__table__.drop(engine, checkfirst=True)

    logger.info("Dropping corner_statistics table...")
    CornerStatistics.__table__.drop(engine, checkfirst=True)

    logger.info("Dropping team_id_mappings table...")
    TeamIDMapping.__table__.drop(engine, checkfirst=True)

    logger.warning("✅ Rollback completed")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        confirmation = input("⚠️  Are you sure you want to rollback? (yes/no): ")
        if confirmation.lower() == "yes":
            rollback_migration()
        else:
            print("Rollback cancelled")
    else:
        run_migration()
```

---

## 🧪 Testing Strategy

### Tests Unitarios

```python
"""
Unit tests for FootyStatsClient
"""
import pytest
from unittest.mock import Mock, patch
from src.api.footystats_client import FootyStatsClient


class TestFootyStatsClient:
    """Test suite for FootyStatsClient"""

    @pytest.fixture
    def client(self):
        """Fixture que crea un cliente"""
        return FootyStatsClient()

    def test_initialization(self, client):
        """Test que el cliente se inicializa correctamente"""
        assert client.api_key is not None
        assert client.BASE_URL == "https://api.football-data-api.com"

    @patch('requests.get')
    def test_make_request_success(self, mock_get, client):
        """Test de request exitoso"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"test": "value"}}
        mock_get.return_value = mock_response

        # Ejecutar
        result = client._make_request("test-endpoint")

        # Verificar
        assert result == {"data": {"test": "value"}}
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_make_request_rate_limit(self, mock_get, client):
        """Test de manejo de rate limit"""
        # Mock response 429
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = Exception("Rate limit")
        mock_get.return_value = mock_response

        # Verificar que lanza excepción
        with pytest.raises(Exception):
            client._make_request("test-endpoint")

    def test_get_corner_stats_parsing(self, client):
        """Test de parseo de estadísticas de córners"""
        # Mock data
        match_data = {
            "team_a_corners": 5,
            "team_b_corners": 7,
            "pre_match_average_corners": 10.5
        }

        # Mock get_match_stats
        with patch.object(client, 'get_match_stats', return_value=match_data):
            result = client.get_corner_stats(12345)

            assert result["team_a_corners"] == 5
            assert result["team_b_corners"] == 7
            assert result["total_corners"] == 12
            assert result["pre_match_average_corners"] == 10.5


class TestCornerAnalyzer:
    """Test suite for CornerAnalyzer"""

    def test_calculate_expected_corners(self):
        """Test de cálculo de córners esperados"""
        from src.analyzers.corner_analyzer import CornerAnalyzer

        home_avg = 6.0
        away_avg = 5.0
        league_avg = 10.5

        expected_home, expected_away = CornerAnalyzer.calculate_expected_corners(
            home_avg, away_avg, league_avg
        )

        # Verificar que los resultados son razonables
        assert expected_home > 0
        assert expected_away > 0
        assert expected_home + expected_away <= league_avg * 1.5  # Sanity check

    def test_calculate_total_corners_probability(self):
        """Test de cálculo de probabilidades"""
        from src.analyzers.corner_analyzer import CornerAnalyzer

        probs = CornerAnalyzer.calculate_total_corners_probability(
            expected_home=5.5,
            expected_away=5.0,
            thresholds=[9.5, 10.5]
        )

        # Verificar estructura
        assert 9.5 in probs
        assert 10.5 in probs
        assert "over" in probs[9.5]
        assert "under" in probs[9.5]

        # Verificar que suman 1
        assert abs(probs[9.5]["over"] + probs[9.5]["under"] - 1.0) < 0.01

    def test_detect_value_bets(self):
        """Test de detección de value bets"""
        from src.analyzers.corner_analyzer import CornerAnalyzer

        probabilities = {
            9.5: {"over": 0.70, "under": 0.30}
        }

        market_odds = {
            9.5: {"over": 1.80, "under": 2.20}  # Implied: 0.556, 0.455
        }

        value_bets = CornerAnalyzer.detect_corner_value_bets(
            probabilities, market_odds, minimum_edge=0.05
        )

        # Debería detectar value bet en "over"
        # 0.70 - 0.556 = 0.144 edge (> 0.05)
        assert len(value_bets) > 0
        assert any(vb["is_value"] for vb in value_bets if vb["market"] == "over")
```

---

## 📈 Métricas y Monitoreo

### KPIs para Medir Éxito

```python
# src/utils/metrics.py

class CornerMetrics:
    """Track corner prediction metrics"""

    @staticmethod
    def track_prediction_accuracy(
        predicted_total: float,
        actual_total: int
    ) -> float:
        """
        Calcula accuracy de predicción de córners

        Returns:
            Mean Absolute Error (MAE)
        """
        mae = abs(predicted_total - actual_total)
        return mae

    @staticmethod
    def track_value_bet_roi(
        value_bets: List[Dict],
        outcomes: List[bool]
    ) -> Dict:
        """
        Calcula ROI de value bets de córners

        Returns:
            {
                "total_bets": 50,
                "won": 32,
                "lost": 18,
                "win_rate": 0.64,
                "roi": 0.12  # 12% ROI
            }
        """
```

### Dashboard de Métricas

```
┌─────────────────────────────────────────────────┐
│         CORNER PREDICTIONS DASHBOARD            │
├─────────────────────────────────────────────────┤
│                                                 │
│  📊 Precisión de Predicciones                   │
│  ├─ MAE: 1.2 córners                           │
│  ├─ Over 9.5 accuracy: 78%                     │
│  └─ Over 10.5 accuracy: 72%                    │
│                                                 │
│  💰 Value Bets Detectados                       │
│  ├─ Total: 127 value bets                      │
│  ├─ High confidence: 45                         │
│  └─ Win rate: 64%                              │
│                                                 │
│  📈 ROI                                         │
│  ├─ Corner bets: +12%                          │
│  ├─ Combined strategy: +18%                    │
│  └─ Best threshold: Over 9.5                   │
│                                                 │
│  🔧 API Usage                                   │
│  ├─ FootyStats calls today: 48/1800           │
│  ├─ Cache hit rate: 85%                        │
│  └─ Average latency: 245ms                     │
└─────────────────────────────────────────────────┘
```

---

## ⚠️ Riesgos y Mitigaciones

### Tabla de Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Diferencia en IDs** | 🟡 Alta | Alto | Sistema de mapping robusto, documentado |
| **Rate limit excedido** | 🟢 Baja | Medio | Rate limiter, cache agresivo |
| **API no disponible** | 🟡 Media | Medio | Fallbacks, sistema funciona sin FootyStats |
| **Datos inconsistentes** | 🟡 Media | Medio | Validación de datos, logs detallados |
| **Costo adicional** | 🟢 Baja | Bajo | Plan Hobby suficiente, monitoreo de uso |
| **Complejidad añadida** | 🟡 Media | Medio | Implementación por fases, tests exhaustivos |

### Estrategias de Fallback

```python
# src/api/api_manager.py

def get_fixture_data_with_fallback(self, fixture_id: int) -> Dict:
    """
    Obtiene datos de fixture con fallback strategy
    """
    data = {}

    # Siempre intentar API-Football primero (principal)
    try:
        data["primary"] = self.api_football.get_fixture_state(fixture_id)
    except Exception as e:
        logger.error(f"API-Football failed: {e}")
        data["primary"] = None

    # Intentar FootyStats (complementario)
    try:
        data["corners"] = self.footystats.get_corner_stats(fixture_id)
    except Exception as e:
        logger.warning(f"FootyStats failed, continuing without corner data: {e}")
        data["corners"] = None  # NO CRÍTICO

    return data
```

---

## 📚 Documentación para Usuario Final

### Guía Rápida de Córners

```markdown
# 🎯 Guía de Predicciones de Córners

## ¿Qué son las predicciones de córners?

El bot ahora analiza estadísticas de córners y detecta value bets en mercados como:
- Over/Under 8.5 córners
- Over/Under 9.5 córners
- Over/Under 10.5 córners
- Over/Under 11.5 córners

## Comandos Disponibles

### /corners_stats <fixture_id>
Muestra análisis de córners para un partido específico

**Ejemplo**:
```
/corners_stats 12345

📊 ANÁLISIS DE CÓRNERS
─────────────────────
⚽ Barcelona vs Real Madrid

Promedios:
├─ Barcelona (L): 6.8 córners/partido
├─ Real Madrid (V): 5.6 córners/partido
└─ Liga: 10.5 córners/partido

Predicción:
├─ Total esperado: 11.2 córners
├─ Over 9.5: 72% ✅
├─ Over 10.5: 58%
└─ Over 11.5: 42%

🎯 VALUE BET DETECTADO
Over 9.5 @ 1.85 (Edge: 14%)
Stake sugerido: 3% del bankroll
```

### /corner_trends <team_id>
Muestra tendencias históricas de un equipo

### /analizar <fixture_id>
Ahora incluye análisis de córners automáticamente
```

---

## ✅ Checklist de Implementación

### Pre-Implementation

- [ ] Crear cuenta FootyStats
- [ ] Suscribirse al plan Hobby
- [ ] Obtener y documentar API Key
- [ ] Revisar documentación oficial completa
- [ ] Mapear IDs de equipos (API-Football ↔ FootyStats)

### Fase 1: Foundation

- [ ] Crear FootyStatsClient
- [ ] Implementar rate limiter
- [ ] Tests de conectividad
- [ ] Actualizar Config con nuevas variables
- [ ] Documentar en .env.example

### Fase 2: Core Endpoints

- [ ] Implementar get_match_stats()
- [ ] Implementar get_team_stats()
- [ ] Implementar get_league_season()
- [ ] Sistema de cache
- [ ] Tests unitarios de endpoints

### Fase 3: Corner Analyzer

- [ ] Crear CornerStatistics model
- [ ] Crear CornerValueBet model
- [ ] Migrar base de datos
- [ ] Implementar CornerAnalyzer
- [ ] Integrar con BotService

### Fase 4: User Interface

- [ ] Formatear mensajes de córners
- [ ] Implementar /corners_stats
- [ ] Implementar /corner_trends
- [ ] Actualizar /analizar
- [ ] Tests de comandos

### Fase 5: Optimization

- [ ] Optimizar queries
- [ ] Error handling robusto
- [ ] Documentación completa
- [ ] Métricas y monitoreo
- [ ] Testing end-to-end

### Post-Implementation

- [ ] Deploy a production
- [ ] Monitorear métricas
- [ ] Ajustar configuración según resultados
- [ ] Documentar learnings
- [ ] Planear Fase 6 (features avanzadas)

---

## 🎓 Conclusiones y Recomendaciones

### ✅ VIABILIDAD: ALTA

FootyStats API es una excelente adición al bot:

1. **✅ Datos Únicos**: Córners detallados que API-Football no ofrece
2. **✅ Complementario**: No reemplaza API-Football, lo complementa
3. **✅ Costo-Beneficio**: Plan Hobby (£29.99/mes) es suficiente
4. **✅ Bajo Riesgo**: Rate limits suficientes, sistema funciona sin FootyStats
5. **✅ Alto Valor**: Abre nuevos mercados de apuestas (córners)

### 🎯 ESTRATEGIA RECOMENDADA

**Integración Complementaria**:
- API-Football: Tiempo real, live updates, fixtures
- FootyStats: Pre-match córners, análisis histórico

**Implementación Incremental**:
- Comenzar con Fase 1-3 (Foundation + Core + Analyzer)
- Validar utilidad con usuarios
- Continuar con Fase 4-5 según feedback

**Enfoque en Value**:
- Priorizar detección de value bets en córners
- Combinar con análisis de goles para estrategias avanzadas
- Monitorear ROI constantemente

### 📋 Próximos Pasos Inmediatos

1. ✅ **Revisar** este documento completo con el equipo
2. ✅ **Aprobar** arquitectura e integración propuesta
3. ✅ **Crear cuenta** FootyStats y obtener API key
4. ✅ **Comenzar Fase 1**: Foundation & Setup
5. ✅ **Iterar** semana a semana según el plan

---

**Documento creado**: 2025-11-05
**Autor**: Claude AI Assistant
**Versión**: 1.0
**Estado**: 🟢 Listo para implementación

---

## 📞 Soporte y Referencias

- **FootyStats API Docs**: https://footystats.org/api/documentations/
- **FootyStats Pricing**: https://footystats.org/api/
- **Corner Stats Page**: https://footystats.org/stats/corner-stats
- **Este Proyecto**: docs/FOOTYSTATS_INTEGRATION_GUIDE.md

**¿Preguntas?** Consulta este documento o la documentación oficial de FootyStats.
