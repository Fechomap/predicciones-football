# 🔴 Investigación: Predicciones en Tiempo Real Durante Partidos en Vivo

## 📋 Resumen Ejecutivo

Esta investigación analiza las opciones para implementar un sistema robusto de **predicciones en tiempo real** durante partidos en vivo, permitiendo consultas múltiples sobre la marcha del partido con predicciones actualizadas.

---

## 🎯 Objetivo

Diseñar un sistema que permita:
1. **Monitorear partidos en vivo** activamente
2. **Generar predicciones actualizadas** cada N minutos durante el partido
3. **Consultar bajo demanda** el estado actual y predicciones
4. **Mantener un sistema robusto** sin exceder límites de la API
5. **Optimizar costos** minimizando llamadas innecesarias

---

## 📊 Análisis del Sistema Actual

### ✅ Fortalezas Actuales

```
┌─────────────────────────────────────────────────────┐
│           ARQUITECTURA ACTUAL (Pre-Match)           │
├─────────────────────────────────────────────────────┤
│ 1. Rate Limiter: 250 req/min (robusto)            │
│ 2. Cache en PostgreSQL (optimizado)                │
│ 3. Modelo Poisson (predicciones sólidas)           │
│ 4. Sistema de alertas (funcional)                  │
│ 5. Fixtures Service (bien diseñado)                │
└─────────────────────────────────────────────────────┘
```

### 🔍 Limitaciones Identificadas

1. **Enfoque Pre-Match**: Sistema diseñado para alertas ANTES del partido
2. **Cache Estático**: Los datos cacheados no se actualizan durante partidos en vivo
3. **Sin Monitoreo Live**: No hay seguimiento de partidos en curso
4. **Predicciones Estáticas**: No se recalculan predicciones con datos actualizados del partido

---

## 🌐 Capacidades de API-Football

### 📡 Datos en Tiempo Real Disponibles

Según la investigación de API-Football:

| Característica | Detalle |
|---------------|---------|
| **Frecuencia de actualización** | ⏱️ Cada **15 segundos** |
| **Datos en vivo** | ✅ Scores, eventos, estadísticas |
| **Eventos** | ⚽ Goles, 🟨🟥 Tarjetas, 🔄 Sustituciones |
| **Estadísticas live** | 📊 Posesión, tiros, corners, etc. |
| **Estados del partido** | LIVE, HT, 2H, ET, P, FT, etc. |

### 🔑 Endpoints Clave para Live Data

```python
# 1. Fixtures con status LIVE
GET /fixtures?live=all                    # Todos los partidos en vivo
GET /fixtures?live={league_id}            # Partidos en vivo de una liga
GET /fixtures?id={fixture_id}             # Estado actual de un partido

# 2. Eventos del partido
GET /fixtures/events?fixture={fixture_id} # Eventos (goles, tarjetas, etc.)

# 3. Estadísticas en vivo
GET /fixtures/statistics?fixture={fixture_id}  # Stats actualizadas

# 4. Line-ups (alineaciones)
GET /fixtures/lineups?fixture={fixture_id}     # Jugadores en cancha
```

---

## 🏗️ Arquitectura Propuesta para Live Predictions

### 🎨 Diseño General

```
┌─────────────────────────────────────────────────────────────┐
│                   LIVE PREDICTION SYSTEM                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐
│  Live Monitor   │───▶│  Prediction      │───▶│  Telegram   │
│   (Scheduler)   │    │   Recalculator   │    │  Notifier   │
└────────┬────────┘    └──────────────────┘    └─────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│              Live Match State Database                       │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Fixture ID │ Minute │ Score │ Events │ Last Update │     │
│  ├────────────────────────────────────────────────────┤     │
│  │   12345    │   45'  │ 1-0   │ [...]  │ 14:32:15   │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘

         ▲                          ▲
         │                          │
    ┌────┴─────┐              ┌────┴──────┐
    │   API    │              │   User    │
    │ Football │              │  Request  │
    └──────────┘              └───────────┘
```

### 🔧 Componentes Nuevos

#### 1. **LiveMatchMonitor** (Nuevo servicio)

```python
# src/services/live_match_monitor.py

class LiveMatchMonitor:
    """
    Monitorea partidos en vivo y actualiza predicciones
    """

    def __init__(self):
        self.active_matches = {}  # {fixture_id: LiveMatchState}
        self.update_interval = 5  # minutos entre actualizaciones

    async def start_monitoring(self, fixture_id: int):
        """Comienza a monitorear un partido"""

    async def stop_monitoring(self, fixture_id: int):
        """Detiene el monitoreo de un partido"""

    async def update_live_predictions(self):
        """Actualiza predicciones para todos los partidos activos"""

    async def get_live_state(self, fixture_id: int):
        """Obtiene el estado actual de un partido"""
```

**Responsabilidades**:
- Mantener lista de partidos en vivo siendo monitoreados
- Actualizar datos cada N minutos
- Recalcular predicciones con datos actualizados
- Almacenar histórico de predicciones durante el partido

#### 2. **LivePredictionEngine** (Nuevo analizador)

```python
# src/analyzers/live_prediction_engine.py

class LivePredictionEngine:
    """
    Genera predicciones ajustadas según el estado actual del partido
    """

    def calculate_live_probabilities(
        self,
        current_score: Tuple[int, int],
        current_minute: int,
        pre_match_expected_goals: Tuple[float, float],
        events: List[Dict]
    ) -> Dict:
        """
        Calcula probabilidades ajustadas basándose en:
        - Marcador actual
        - Minuto del partido
        - Goles esperados pre-partido
        - Eventos ocurridos (tarjetas rojas, etc.)
        """

    def adjust_for_game_state(
        self,
        probabilities: Dict,
        game_state: Dict
    ) -> Dict:
        """
        Ajusta predicciones basándose en:
        - Tarjetas rojas (ventaja numérica)
        - Posesión dominante
        - Tendencia de ataques
        """
```

**Algoritmo de Predicción Live**:

```
1. Obtener predicción pre-partido (Poisson)
2. Ajustar por marcador actual y tiempo restante
3. Aplicar factores de contexto:
   - Tarjetas rojas → Recalcular con ventaja numérica
   - Minuto 80+ → Mayor peso a resultado actual
   - Equipo perdiendo → Mayor probabilidad de arriesgar
4. Calcular nuevas probabilidades 1X2
5. Detectar value bets con odds actualizadas
```

#### 3. **LiveMatchState** (Nuevo modelo de datos)

```python
# src/database/models.py

class LiveMatchState(Base):
    __tablename__ = "live_match_states"

    id = Column(Integer, primary_key=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"))

    # Estado del partido
    minute = Column(Integer)
    period = Column(String)  # 1H, 2H, HT, ET, P
    score_home = Column(Integer)
    score_away = Column(Integer)

    # Estadísticas en vivo
    possession_home = Column(Float)
    possession_away = Column(Float)
    shots_home = Column(Integer)
    shots_away = Column(Integer)

    # Eventos importantes
    red_cards_home = Column(Integer, default=0)
    red_cards_away = Column(Integer, default=0)

    # Predicciones actualizadas
    live_home_prob = Column(Float)
    live_draw_prob = Column(Float)
    live_away_prob = Column(Float)

    # Metadatos
    last_update = Column(DateTime, default=datetime.utcnow)
    snapshot_number = Column(Integer)  # 1, 2, 3... (cada 5 min)
```

---

## 📈 Estrategias de Actualización

### ✅ Opción 1: **Polling Inteligente** (RECOMENDADO)

```python
# Actualización cada N minutos solo para partidos monitoreados

async def intelligent_polling():
    """
    Estrategia de polling optimizada
    """
    while True:
        # 1. Obtener lista de partidos en vivo (1 API call)
        live_matches = await api.get_fixtures(live="all")

        # 2. Filtrar solo partidos que estamos monitoreando
        monitored = filter_monitored_matches(live_matches)

        # 3. Actualizar cada partido (3 API calls por partido)
        for match in monitored:
            # 3a. Estado del partido (incluido en llamada anterior)
            # 3b. Eventos
            events = await api.get_events(match.id)
            # 3c. Estadísticas
            stats = await api.get_statistics(match.id)

            # 4. Recalcular predicciones
            new_predictions = live_engine.calculate_live_probabilities(
                current_score=(match.score_home, match.score_away),
                current_minute=match.minute,
                events=events,
                stats=stats
            )

            # 5. Guardar en BD
            save_live_state(match.id, new_predictions)

            # 6. Notificar si hay cambios significativos
            if significant_change(new_predictions):
                await notify_users(match.id, new_predictions)

        # Esperar 5 minutos
        await asyncio.sleep(300)
```

**Consumo de API**:
- 1 partido monitoreado: ~3 calls cada 5 min = **36 calls/hora**
- 3 partidos simultáneos: ~9 calls cada 5 min = **108 calls/hora**
- Límite: 250 calls/min = **15,000 calls/hora** ✅ Muy por debajo del límite

### ⚡ Opción 2: **WebSockets** (Futuro)

```python
# Conexión persistente para updates en tiempo real (NO disponible en API-Football)

# Nota: API-Football no ofrece WebSockets en su plan actual
# Alternativas:
# - Sportmonks API (ofrece WebSockets en planes premium)
# - Implementar polling pero con cache de 15 segundos
```

### 🎚️ Opción 3: **Híbrido con Niveles de Actualización**

```python
# Diferentes frecuencias según importancia del partido

UPDATE_FREQUENCIES = {
    "high_priority": 3,    # Cada 3 minutos (partidos con value bets activos)
    "medium_priority": 5,  # Cada 5 minutos (partidos monitoreados)
    "low_priority": 10,    # Cada 10 minutos (partidos de bajo interés)
}
```

---

## 💾 Gestión de Caché para Live Data

### 🚫 Cambio de Estrategia: Cache Corto

```python
# ANTES (Pre-match): Cache de 3 horas
fixtures_cache.set(key, data, ttl_seconds=10800)

# AHORA (Live): Cache de 15-30 segundos
live_cache.set(key, data, ttl_seconds=30)  # Datos muy volátiles
```

### 🗄️ Almacenamiento en BD

```sql
-- Tabla para histórico de estados durante el partido
CREATE TABLE live_match_states (
    id SERIAL PRIMARY KEY,
    fixture_id INT REFERENCES fixtures(id),
    minute INT,
    score_home INT,
    score_away INT,
    live_home_prob FLOAT,
    live_draw_prob FLOAT,
    live_away_prob FLOAT,
    snapshot_number INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índice para consultas rápidas
CREATE INDEX idx_fixture_snapshot ON live_match_states(fixture_id, snapshot_number DESC);
```

**Beneficios**:
- Histórico completo de predicciones durante el partido
- Análisis post-partido de precisión
- Gráficos de evolución de probabilidades
- Machine Learning futuro con datos reales

---

## 🎮 Interfaz de Usuario (Telegram)

### 📱 Nuevos Comandos

```python
# Comandos para partidos en vivo

/live              # Mostrar partidos en vivo siendo monitoreados
/monitor {id}      # Comenzar a monitorear un partido
/stop_monitor {id} # Detener monitoreo
/live_analysis {id} # Ver análisis en vivo de un partido
/predictions_history {id}  # Ver evolución de predicciones
```

### 💬 Menú Interactivo Mejorado

```
⚽ PARTIDOS EN VIVO
─────────────────────
🔴 Barcelona vs Real Madrid (67')
   Score: 2-1
   Predicción Actual:
   - Barcelona: 65% (+15% vs pre-match)
   - Empate: 20% (-10% vs pre-match)
   - Real Madrid: 15% (-5% vs pre-match)

   🎯 VALUE BET DETECTADO
   Empate @ 5.50 (Edge: 10%)

   [📊 Ver Detalles] [🔕 Detener Alertas]

─────────────────────
🟢 Liverpool vs Arsenal (15')
   Score: 0-0
   Predicción: Sin cambios significativos

   [📊 Ver Detalles] [🔕 Detener Monitoreo]

[➕ Monitorear Otro Partido]
```

### 🔔 Notificaciones Automáticas

```python
# Enviar alerta cuando cambian significativamente las probabilidades

async def check_significant_change(old_probs, new_probs):
    """
    Notificar si:
    - Cambio > 15% en cualquier resultado
    - Nuevo value bet detectado
    - Tarjeta roja (cambio de contexto)
    """
    change = abs(new_probs["home"] - old_probs["home"])

    if change > 0.15:  # Cambio del 15%
        await notify_probability_shift(fixture_id, old_probs, new_probs)
```

---

## 🔢 Estimación de Costos de API

### 📊 Escenario Base: 3 Partidos Simultáneos

```
Configuración:
- 3 partidos en vivo monitoreados
- Actualización cada 5 minutos
- Duración promedio: 105 minutos (90 + 15 extra time)

Cálculos:
- Updates por partido: 105 / 5 = 21 updates
- API calls por update: 2 (events + statistics)
- Total por partido: 21 * 2 = 42 calls
- Total 3 partidos: 42 * 3 = 126 calls

Llamadas totales en un día con 3 partidos: ~150 calls
```

### 💰 Comparación con Sistema Actual

| Concepto | Sistema Actual | Con Live Predictions |
|----------|---------------|---------------------|
| **Pre-match** | 48 calls/día | 48 calls/día |
| **Live monitoring** | 0 calls | ~150 calls/día (3 partidos) |
| **Total diario** | 48 calls | ~200 calls |
| **Límite API** | 300 calls/min | 300 calls/min |
| **% Utilizado** | <1% | <2% |
| **Margen** | ✅ Enorme | ✅ Enorme |

**Conclusión**: ✅ **El sistema es completamente viable** sin riesgo de exceder límites.

---

## 🚀 Plan de Implementación Sugerido

### 📅 Fase 1: Foundation (Semana 1-2)

1. ✅ **Crear modelo LiveMatchState** en database
2. ✅ **Implementar LiveMatchMonitor** service básico
3. ✅ **Agregar endpoints live a APIFootballClient**
4. ✅ **Tests unitarios** de componentes nuevos

### 📅 Fase 2: Core Live Engine (Semana 2-3)

5. ✅ **Implementar LivePredictionEngine**
6. ✅ **Algoritmo de ajuste de probabilidades**
7. ✅ **Sistema de detección de cambios significativos**
8. ✅ **Integrar con sistema de notificaciones**

### 📅 Fase 3: User Interface (Semana 3-4)

9. ✅ **Comandos Telegram para live**
10. ✅ **Menús interactivos actualizados**
11. ✅ **Sistema de subscripción a partidos**
12. ✅ **Formateo de mensajes live**

### 📅 Fase 4: Optimization & Polish (Semana 4-5)

13. ✅ **Optimización de cache**
14. ✅ **Rate limiting inteligente**
15. ✅ **Dashboard de métricas**
16. ✅ **Documentación completa**

### 📅 Fase 5: Advanced Features (Futuro)

17. 🔮 **Gráficos de evolución de probabilidades**
18. 🔮 **Machine Learning con datos históricos**
19. 🔮 **Alertas personalizadas por usuario**
20. 🔮 **Integración con WebSockets (si API lo soporta)**

---

## ⚠️ Consideraciones y Riesgos

### 🚨 Riesgos Técnicos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| **API rate limiting** | Alto | Polling inteligente cada 5 min, cache de 30s |
| **Costo de API** | Medio | Monitoreo selectivo, límite de partidos simultáneos |
| **Latencia de datos** | Bajo | API actualiza cada 15s, aceptable para nuestro caso |
| **Complejidad** | Medio | Implementación incremental, tests exhaustivos |

### 💡 Mejores Prácticas

```python
# 1. Límite de partidos simultáneos
MAX_LIVE_MATCHES = 5  # No exceder

# 2. Auto-detener monitoreo al finalizar
async def auto_cleanup():
    for match in monitored_matches:
        if match.status == "FT":
            await stop_monitoring(match.id)

# 3. Fallback si API falla
try:
    live_data = await api.get_live_state(fixture_id)
except APIError:
    # Usar última predicción conocida
    live_data = db.get_last_live_state(fixture_id)

# 4. Throttling por usuario
@rate_limit(max_requests=10, window=60)  # 10 consultas/min por usuario
async def handle_live_request(user_id, fixture_id):
    ...
```

---

## 📊 Métricas de Éxito

### KPIs Sugeridos

1. **Precisión de Predicciones Live**
   - % de aciertos en predicciones live vs pre-match
   - MAE (Mean Absolute Error) de probabilidades

2. **Engagement de Usuarios**
   - Número de partidos monitoreados por día
   - Consultas live por usuario
   - Tiempo promedio de seguimiento

3. **Rendimiento Técnico**
   - API calls por partido
   - Latencia de actualización
   - Tasa de error en llamadas API

4. **Value Bets Live**
   - Value bets detectados durante partidos
   - ROI teórico de apuestas live vs pre-match

---

## 🎓 Conclusiones y Recomendaciones

### ✅ VIABILIDAD: **ALTA**

El sistema es completamente viable técnica y económicamente:

1. **API-Football proporciona todos los datos necesarios** (actualización cada 15s)
2. **El límite de API es suficiente** (>99% de margen disponible)
3. **La arquitectura actual es sólida** (solo requiere extensión, no refactoring)
4. **El modelo Poisson puede adaptarse** para predicciones en vivo

### 🎯 RECOMENDACIONES

#### Corto Plazo (1-2 meses)

1. ✅ **Implementar Polling Inteligente** (Opción 1)
   - Más simple
   - Suficiente para MVP
   - Bajo riesgo

2. ✅ **Comenzar con monitoreo manual**
   - Usuario inicia monitoreo con `/monitor {id}`
   - Limitar a 3 partidos simultáneos
   - Validar demanda real

3. ✅ **Enfocarse en UX simple**
   - Notificaciones claras
   - Fácil iniciar/detener monitoreo
   - Información digestible

#### Mediano Plazo (3-6 meses)

4. 🔮 **Auto-monitoreo inteligente**
   - Monitorear automáticamente partidos con value bets pre-match
   - ML para predecir qué partidos tendrán oportunidades live

5. 🔮 **Dashboard web**
   - Visualización de evolución de probabilidades
   - Gráficos interactivos
   - Histórico de precisión

#### Largo Plazo (6+ meses)

6. 🔮 **Machine Learning avanzado**
   - Entrenar modelos con datos históricos live
   - Predecir momentum de equipos
   - Detectar patrones de remontadas

7. 🔮 **WebSockets si disponible**
   - Migrar a API con soporte WebSocket
   - Updates en tiempo real (<1s)
   - Reducir carga de polling

---

## 📚 Referencias y Recursos

### APIs Investigadas

1. **API-Football** (Actual)
   - Docs: https://www.api-football.com/documentation-v3
   - Actualización: 15 segundos
   - Plan actual: Suficiente

2. **Sportmonks** (Alternativa)
   - WebSockets disponibles
   - Mayor costo
   - Evaluación futura si se requiere

3. **Live-Score API** (Alternativa)
   - Enfocado en live scores
   - Menos estadísticas
   - Backup option

### Papers y Teoría

1. **In-Play Betting Algorithms**
   - Poisson ajustado por tiempo
   - Modelos de regresión dinámica

2. **Live Sports Prediction**
   - Bayesian updating
   - Dynamic probability adjustment

---

## 👥 Próximos Pasos

1. **Revisar este documento con el equipo**
2. **Aprobar arquitectura propuesta**
3. **Priorizar fases de implementación**
4. **Asignar recursos y timeline**
5. **Comenzar Fase 1**

---

**Documento creado**: 2025-11-05
**Autor**: Claude (AI Assistant)
**Versión**: 1.0
**Estado**: 🟢 Listo para revisión
