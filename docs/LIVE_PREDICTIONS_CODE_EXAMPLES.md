# 💻 Ejemplos de Código: Predicciones en Tiempo Real

Esta guía complementa el documento de investigación con **ejemplos de código concretos** para implementar el sistema de predicciones en vivo.

---

## 📁 Estructura de Archivos Nuevos

```
src/
├── analyzers/
│   └── live_prediction_engine.py     # NUEVO
├── services/
│   └── live_match_monitor.py         # NUEVO
├── database/
│   └── models.py                      # MODIFICAR (agregar LiveMatchState)
├── api/
│   └── api_football.py                # MODIFICAR (agregar métodos live)
└── notifications/
    └── telegram_handlers.py           # MODIFICAR (agregar comandos live)
```

---

## 🗄️ 1. Modelo de Base de Datos

### `src/database/models.py`

```python
"""Add LiveMatchState model"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class LiveMatchState(Base):
    """
    Almacena el estado de un partido en vivo en un momento dado
    Se crea un snapshot cada N minutos durante el partido
    """
    __tablename__ = "live_match_states"

    id = Column(Integer, primary_key=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False)

    # Estado temporal del partido
    minute = Column(Integer)  # Minuto actual (0-90+)
    period = Column(String(10))  # 1H, HT, 2H, ET, P, FT
    elapsed_time = Column(Integer)  # Tiempo total transcurrido

    # Marcador
    score_home = Column(Integer, default=0)
    score_away = Column(Integer, default=0)

    # Estadísticas del partido
    possession_home = Column(Float)  # % posesión
    possession_away = Column(Float)
    shots_home = Column(Integer, default=0)
    shots_away = Column(Integer, default=0)
    shots_on_target_home = Column(Integer, default=0)
    shots_on_target_away = Column(Integer, default=0)
    corners_home = Column(Integer, default=0)
    corners_away = Column(Integer, default=0)

    # Eventos críticos
    red_cards_home = Column(Integer, default=0)
    red_cards_away = Column(Integer, default=0)
    yellow_cards_home = Column(Integer, default=0)
    yellow_cards_away = Column(Integer, default=0)

    # Predicciones recalculadas
    live_home_prob = Column(Float)  # Probabilidad ajustada de victoria local
    live_draw_prob = Column(Float)  # Probabilidad ajustada de empate
    live_away_prob = Column(Float)  # Probabilidad ajustada de victoria visitante

    # Probabilidades pre-match (para comparación)
    pre_match_home_prob = Column(Float)
    pre_match_draw_prob = Column(Float)
    pre_match_away_prob = Column(Float)

    # Cambios en probabilidades
    prob_change_home = Column(Float)  # Cambio vs pre-match
    prob_change_draw = Column(Float)
    prob_change_away = Column(Float)

    # Metadatos
    snapshot_number = Column(Integer)  # 1, 2, 3... (contador de updates)
    last_api_update = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación con fixture
    fixture = relationship("Fixture", backref="live_states")

    def __repr__(self):
        return (
            f"<LiveMatchState fixture_id={self.fixture_id} "
            f"minute={self.minute} score={self.score_home}-{self.score_away}>"
        )


class MonitoredMatch(Base):
    """
    Registro de partidos que están siendo monitoreados activamente
    """
    __tablename__ = "monitored_matches"

    id = Column(Integer, primary_key=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), unique=True)
    user_id = Column(String)  # Telegram user ID que solicitó el monitoreo

    # Estado de monitoreo
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)

    # Configuración
    update_interval = Column(Integer, default=5)  # Minutos entre updates
    notify_on_goal = Column(Boolean, default=True)
    notify_on_red_card = Column(Boolean, default=True)
    notify_on_prob_change = Column(Boolean, default=True)
    min_prob_change = Column(Float, default=0.15)  # 15% cambio mínimo

    # Relación
    fixture = relationship("Fixture")

    def __repr__(self):
        return f"<MonitoredMatch fixture_id={self.fixture_id} active={self.is_active}>"
```

---

## 🔌 2. Extensión del Cliente API

### `src/api/api_football.py` (agregar métodos)

```python
"""Add live match methods to APIFootballClient"""

def get_live_fixtures(self, league_id: Optional[int] = None) -> List[Dict]:
    """
    Get all live fixtures or for a specific league

    Args:
        league_id: Optional league ID to filter

    Returns:
        List of live fixtures
    """
    params = {"live": "all" if not league_id else str(league_id)}

    logger.info(f"Fetching live fixtures{f' for league {league_id}' if league_id else ''}")
    response = self._make_request("fixtures", params)

    return response.get("response", [])


def get_fixture_live_state(self, fixture_id: int) -> Dict:
    """
    Get current state of a specific fixture (live or finished)

    Args:
        fixture_id: Fixture ID

    Returns:
        Fixture data with current state
    """
    params = {"id": fixture_id}

    logger.info(f"Fetching live state for fixture {fixture_id}")
    response = self._make_request("fixtures", params)

    fixtures = response.get("response", [])
    return fixtures[0] if fixtures else {}


def get_fixture_events(self, fixture_id: int) -> List[Dict]:
    """
    Get all events for a fixture (goals, cards, substitutions)

    Args:
        fixture_id: Fixture ID

    Returns:
        List of events
    """
    params = {"fixture": fixture_id}

    logger.info(f"Fetching events for fixture {fixture_id}")
    response = self._make_request("fixtures/events", params)

    return response.get("response", [])


def get_live_statistics(self, fixture_id: int) -> List[Dict]:
    """
    Get live statistics for a fixture
    NOTE: This endpoint may not have data until the match starts

    Args:
        fixture_id: Fixture ID

    Returns:
        Statistics data
    """
    return self.get_fixture_statistics(fixture_id)  # Usa el método existente
```

---

## 🧮 3. Motor de Predicciones en Vivo

### `src/analyzers/live_prediction_engine.py`

```python
"""Live prediction engine for in-play matches"""
from typing import Dict, Tuple, List
from scipy.stats import poisson
import math

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class LivePredictionEngine:
    """
    Calcula predicciones ajustadas durante partidos en vivo

    Metodología:
    1. Partir de predicción pre-match (Poisson)
    2. Ajustar por marcador actual y tiempo restante
    3. Aplicar factores de contexto (tarjetas rojas, momentum)
    4. Calcular nuevas probabilidades 1X2
    """

    @staticmethod
    def calculate_live_probabilities(
        current_score: Tuple[int, int],
        current_minute: int,
        pre_match_expected_goals: Tuple[float, float],
        events: List[Dict],
        statistics: Dict = None
    ) -> Dict:
        """
        Calcula probabilidades ajustadas para el resto del partido

        Args:
            current_score: (goles_home, goles_away)
            current_minute: Minuto actual del partido
            pre_match_expected_goals: (expected_home, expected_away) pre-partido
            events: Lista de eventos (para detectar tarjetas rojas)
            statistics: Estadísticas del partido (opcional)

        Returns:
            {
                "live_home_prob": 0.45,
                "live_draw_prob": 0.30,
                "live_away_prob": 0.25,
                "expected_final_home": 1.8,
                "expected_final_away": 1.2
            }
        """
        home_score, away_score = current_score
        pre_match_home, pre_match_away = pre_match_expected_goals

        # 1. Calcular tiempo restante (en fracción)
        time_fraction_remaining = max(0, (90 - current_minute) / 90)

        # 2. Detectar tarjetas rojas
        red_cards_home = sum(1 for e in events if e.get("type") == "Card"
                            and e.get("detail") == "Red Card"
                            and e.get("team", {}).get("name") == "home")

        red_cards_away = sum(1 for e in events if e.get("type") == "Card"
                            and e.get("detail") == "Red Card"
                            and e.get("team", {}).get("name") == "away")

        # 3. Ajustar expectativa de goles restantes
        # Si un equipo tiene tarjeta roja, reducir su expectativa
        home_advantage_factor = 1.0
        away_advantage_factor = 1.0

        if red_cards_home > 0:
            home_advantage_factor = 0.6  # -40% de capacidad ofensiva
        if red_cards_away > 0:
            away_advantage_factor = 0.6

        if red_cards_away > 0 and red_cards_home == 0:
            home_advantage_factor = 1.3  # +30% vs 10 jugadores
        if red_cards_home > 0 and red_cards_away == 0:
            away_advantage_factor = 1.3

        # 4. Estimar goles adicionales esperados
        remaining_home_goals = (
            pre_match_home * time_fraction_remaining * home_advantage_factor
        )
        remaining_away_goals = (
            pre_match_away * time_fraction_remaining * away_advantage_factor
        )

        # 5. Proyectar marcador final esperado
        expected_final_home = home_score + remaining_home_goals
        expected_final_away = away_score + remaining_away_goals

        logger.debug(
            f"Live prediction: Current={home_score}-{away_score}, "
            f"Minute={current_minute}, "
            f"Expected final={expected_final_home:.2f}-{expected_final_away:.2f}"
        )

        # 6. Calcular probabilidades con Poisson para goles restantes
        probs = LivePredictionEngine._calculate_remaining_match_probabilities(
            current_home=home_score,
            current_away=away_score,
            expected_home=remaining_home_goals,
            expected_away=remaining_away_goals
        )

        return {
            "live_home_prob": probs["home_win"],
            "live_draw_prob": probs["draw"],
            "live_away_prob": probs["away_win"],
            "expected_final_home": round(expected_final_home, 2),
            "expected_final_away": round(expected_final_away, 2),
            "time_remaining_pct": round(time_fraction_remaining * 100, 1),
            "context": {
                "red_cards_home": red_cards_home,
                "red_cards_away": red_cards_away,
                "home_advantage_factor": home_advantage_factor,
                "away_advantage_factor": away_advantage_factor
            }
        }

    @staticmethod
    def _calculate_remaining_match_probabilities(
        current_home: int,
        current_away: int,
        expected_home: float,
        expected_away: float,
        max_goals: int = 8
    ) -> Dict[str, float]:
        """
        Calcula probabilidades para el resultado final dado el marcador actual

        Args:
            current_home: Goles actuales del local
            current_away: Goles actuales del visitante
            expected_home: Goles esperados adicionales del local
            expected_away: Goles esperados adicionales del visitante
            max_goals: Máximo de goles adicionales a considerar

        Returns:
            Probabilidades de victoria local, empate, victoria visitante
        """
        home_win_prob = 0.0
        draw_prob = 0.0
        away_win_prob = 0.0

        # Simular todos los posibles marcadores finales
        for add_home in range(max_goals + 1):
            for add_away in range(max_goals + 1):
                # Probabilidad de estos goles adicionales (Poisson)
                prob = (
                    poisson.pmf(add_home, expected_home) *
                    poisson.pmf(add_away, expected_away)
                )

                # Marcador final
                final_home = current_home + add_home
                final_away = current_away + add_away

                # Acumular probabilidades
                if final_home > final_away:
                    home_win_prob += prob
                elif final_home == final_away:
                    draw_prob += prob
                else:
                    away_win_prob += prob

        return {
            "home_win": round(home_win_prob, 4),
            "draw": round(draw_prob, 4),
            "away_win": round(away_win_prob, 4)
        }

    @staticmethod
    def detect_significant_change(
        old_probs: Dict[str, float],
        new_probs: Dict[str, float],
        threshold: float = 0.15
    ) -> Dict:
        """
        Detecta si hubo un cambio significativo en las probabilidades

        Args:
            old_probs: Probabilidades anteriores
            new_probs: Probabilidades nuevas
            threshold: Umbral de cambio (default 15%)

        Returns:
            {
                "has_significant_change": bool,
                "changes": {"home": 0.12, "draw": -0.08, ...},
                "max_change": 0.12
            }
        """
        changes = {
            "home": new_probs.get("live_home_prob", 0) - old_probs.get("live_home_prob", 0),
            "draw": new_probs.get("live_draw_prob", 0) - old_probs.get("live_draw_prob", 0),
            "away": new_probs.get("live_away_prob", 0) - old_probs.get("live_away_prob", 0)
        }

        max_change = max(abs(c) for c in changes.values())
        has_significant_change = max_change >= threshold

        return {
            "has_significant_change": has_significant_change,
            "changes": changes,
            "max_change": round(max_change, 4),
            "threshold": threshold
        }
```

---

## 🔍 4. Monitor de Partidos en Vivo

### `src/services/live_match_monitor.py`

```python
"""Live match monitoring service"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..api import APIFootballClient
from ..database import db_manager, LiveMatchState, MonitoredMatch, Fixture
from ..analyzers import LivePredictionEngine
from ..notifications import TelegramNotifier
from ..utils.logger import setup_logger
from ..utils.config import Config

logger = setup_logger(__name__)


class LiveMatchMonitor:
    """
    Monitorea partidos en vivo y actualiza predicciones periódicamente
    """

    def __init__(self):
        self.api_client = APIFootballClient()
        self.prediction_engine = LivePredictionEngine()
        self.telegram = TelegramNotifier()

        self.is_running = False
        self.update_task = None

        # Cache de predicciones pre-match
        self.pre_match_predictions = {}

        logger.info("LiveMatchMonitor initialized")

    async def start(self):
        """Inicia el monitoreo de partidos en vivo"""
        if self.is_running:
            logger.warning("LiveMatchMonitor already running")
            return

        self.is_running = True
        logger.info("🔴 Starting LiveMatchMonitor...")

        # Iniciar tarea de actualización periódica
        self.update_task = asyncio.create_task(self._update_loop())

    async def stop(self):
        """Detiene el monitoreo"""
        self.is_running = False

        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

        logger.info("LiveMatchMonitor stopped")

    async def _update_loop(self):
        """Loop principal de actualización"""
        while self.is_running:
            try:
                await self._update_all_monitored_matches()

                # Esperar N minutos antes de siguiente actualización
                await asyncio.sleep(Config.LIVE_UPDATE_INTERVAL * 60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                await asyncio.sleep(60)  # Esperar 1 minuto en caso de error

    async def _update_all_monitored_matches(self):
        """Actualiza todos los partidos monitoreados activos"""
        with db_manager.get_session() as session:
            monitored = session.query(MonitoredMatch).filter(
                MonitoredMatch.is_active == True
            ).all()

            logger.info(f"Updating {len(monitored)} monitored matches")

            for match in monitored:
                try:
                    await self._update_match(match.fixture_id)
                except Exception as e:
                    logger.error(f"Error updating fixture {match.fixture_id}: {e}")

    async def _update_match(self, fixture_id: int):
        """
        Actualiza el estado y predicciones de un partido específico

        Args:
            fixture_id: ID del fixture
        """
        logger.debug(f"Updating live state for fixture {fixture_id}")

        # 1. Obtener estado actual del partido
        fixture_data = self.api_client.get_fixture_live_state(fixture_id)

        if not fixture_data:
            logger.warning(f"No data returned for fixture {fixture_id}")
            return

        fixture_info = fixture_data.get("fixture", {})
        status = fixture_info.get("status", {}).get("short", "")

        # Si el partido terminó, detener monitoreo
        if status in ["FT", "AET", "PEN"]:
            logger.info(f"Match {fixture_id} finished, stopping monitoring")
            await self.stop_monitoring(fixture_id)
            return

        # Solo continuar si el partido está en vivo
        if status not in ["1H", "HT", "2H", "ET", "BT", "P", "LIVE"]:
            logger.debug(f"Match {fixture_id} not live yet (status: {status})")
            return

        # 2. Obtener eventos y estadísticas
        events = self.api_client.get_fixture_events(fixture_id)
        statistics = self.api_client.get_live_statistics(fixture_id)

        # 3. Extraer información relevante
        goals = fixture_data.get("goals", {})
        current_score = (goals.get("home", 0), goals.get("away", 0))
        current_minute = fixture_info.get("status", {}).get("elapsed", 0)

        # 4. Obtener predicción pre-match (o usar cache)
        pre_match_probs = await self._get_pre_match_prediction(fixture_id)

        if not pre_match_probs:
            logger.warning(f"No pre-match prediction for fixture {fixture_id}")
            return

        # 5. Calcular predicciones actualizadas
        live_probs = self.prediction_engine.calculate_live_probabilities(
            current_score=current_score,
            current_minute=current_minute,
            pre_match_expected_goals=(
                pre_match_probs.get("expected_home", 1.5),
                pre_match_probs.get("expected_away", 1.5)
            ),
            events=events,
            statistics=statistics
        )

        # 6. Guardar estado en base de datos
        await self._save_live_state(
            fixture_id=fixture_id,
            current_score=current_score,
            current_minute=current_minute,
            period=status,
            events=events,
            statistics=statistics,
            live_probs=live_probs,
            pre_match_probs=pre_match_probs
        )

        # 7. Detectar cambios significativos
        with db_manager.get_session() as session:
            previous_state = session.query(LiveMatchState).filter(
                LiveMatchState.fixture_id == fixture_id
            ).order_by(LiveMatchState.snapshot_number.desc()).offset(1).first()

            if previous_state:
                old_probs = {
                    "live_home_prob": previous_state.live_home_prob,
                    "live_draw_prob": previous_state.live_draw_prob,
                    "live_away_prob": previous_state.live_away_prob
                }

                change_analysis = self.prediction_engine.detect_significant_change(
                    old_probs=old_probs,
                    new_probs=live_probs
                )

                # 8. Notificar si hay cambio significativo
                if change_analysis["has_significant_change"]:
                    await self._notify_probability_change(
                        fixture_id=fixture_id,
                        fixture_data=fixture_data,
                        change_analysis=change_analysis,
                        live_probs=live_probs
                    )

    async def _get_pre_match_prediction(self, fixture_id: int) -> Optional[Dict]:
        """
        Obtiene la predicción pre-match de un fixture

        Args:
            fixture_id: ID del fixture

        Returns:
            Diccionario con predicciones pre-match
        """
        # Buscar en cache
        if fixture_id in self.pre_match_predictions:
            return self.pre_match_predictions[fixture_id]

        # Buscar en BD
        with db_manager.get_session() as session:
            from ..database.models import Prediction

            prediction = session.query(Prediction).filter(
                Prediction.fixture_id == fixture_id
            ).first()

            if prediction:
                pre_match_probs = {
                    "expected_home": prediction.expected_goals_home,
                    "expected_away": prediction.expected_goals_away,
                    "home_prob": prediction.home_probability,
                    "draw_prob": prediction.draw_probability,
                    "away_prob": prediction.away_probability
                }

                # Guardar en cache
                self.pre_match_predictions[fixture_id] = pre_match_probs

                return pre_match_probs

        return None

    async def _save_live_state(
        self,
        fixture_id: int,
        current_score: Tuple[int, int],
        current_minute: int,
        period: str,
        events: List[Dict],
        statistics: Dict,
        live_probs: Dict,
        pre_match_probs: Dict
    ):
        """Guarda el estado actual del partido en la BD"""
        with db_manager.get_session() as session:
            # Contar snapshot number
            last_snapshot = session.query(LiveMatchState).filter(
                LiveMatchState.fixture_id == fixture_id
            ).order_by(LiveMatchState.snapshot_number.desc()).first()

            snapshot_number = (last_snapshot.snapshot_number + 1) if last_snapshot else 1

            # Extraer estadísticas
            stats_dict = self._extract_statistics(statistics)

            # Contar tarjetas rojas
            red_cards = self._count_red_cards(events)

            # Crear nuevo estado
            live_state = LiveMatchState(
                fixture_id=fixture_id,
                minute=current_minute,
                period=period,
                score_home=current_score[0],
                score_away=current_score[1],
                possession_home=stats_dict.get("possession_home"),
                possession_away=stats_dict.get("possession_away"),
                shots_home=stats_dict.get("shots_home"),
                shots_away=stats_dict.get("shots_away"),
                red_cards_home=red_cards["home"],
                red_cards_away=red_cards["away"],
                live_home_prob=live_probs["live_home_prob"],
                live_draw_prob=live_probs["live_draw_prob"],
                live_away_prob=live_probs["live_away_prob"],
                pre_match_home_prob=pre_match_probs.get("home_prob"),
                pre_match_draw_prob=pre_match_probs.get("draw_prob"),
                pre_match_away_prob=pre_match_probs.get("away_prob"),
                prob_change_home=live_probs["live_home_prob"] - pre_match_probs.get("home_prob", 0),
                prob_change_draw=live_probs["live_draw_prob"] - pre_match_probs.get("draw_prob", 0),
                prob_change_away=live_probs["live_away_prob"] - pre_match_probs.get("away_prob", 0),
                snapshot_number=snapshot_number,
                last_api_update=datetime.now(timezone.utc)
            )

            session.add(live_state)
            session.commit()

            logger.debug(f"Saved live state snapshot #{snapshot_number} for fixture {fixture_id}")

    def _extract_statistics(self, statistics: Dict) -> Dict:
        """Extrae estadísticas relevantes de la respuesta de la API"""
        # Implementar parsing de estadísticas
        # La estructura depende de la respuesta real de la API
        return {
            "possession_home": None,
            "possession_away": None,
            "shots_home": None,
            "shots_away": None
        }

    def _count_red_cards(self, events: List[Dict]) -> Dict[str, int]:
        """Cuenta tarjetas rojas de cada equipo"""
        red_cards = {"home": 0, "away": 0}

        for event in events:
            if event.get("type") == "Card" and event.get("detail") == "Red Card":
                team = event.get("team", {}).get("name")
                # Necesitarías lógica para determinar si es home o away
                # Esto depende de la estructura de datos de tu sistema

        return red_cards

    async def _notify_probability_change(
        self,
        fixture_id: int,
        fixture_data: Dict,
        change_analysis: Dict,
        live_probs: Dict
    ):
        """Envía notificación de cambio significativo en probabilidades"""
        # Implementar notificación por Telegram
        logger.info(f"🔔 Significant probability change detected for fixture {fixture_id}")

    async def start_monitoring(self, fixture_id: int, user_id: str):
        """Comienza a monitorear un partido"""
        with db_manager.get_session() as session:
            # Verificar si ya existe
            existing = session.query(MonitoredMatch).filter(
                MonitoredMatch.fixture_id == fixture_id,
                MonitoredMatch.is_active == True
            ).first()

            if existing:
                logger.info(f"Fixture {fixture_id} already being monitored")
                return

            # Crear nuevo monitoreo
            monitored = MonitoredMatch(
                fixture_id=fixture_id,
                user_id=user_id,
                is_active=True
            )

            session.add(monitored)
            session.commit()

            logger.info(f"🎯 Started monitoring fixture {fixture_id} for user {user_id}")

    async def stop_monitoring(self, fixture_id: int):
        """Detiene el monitoreo de un partido"""
        with db_manager.get_session() as session:
            monitored = session.query(MonitoredMatch).filter(
                MonitoredMatch.fixture_id == fixture_id,
                MonitoredMatch.is_active == True
            ).first()

            if monitored:
                monitored.is_active = False
                monitored.stopped_at = datetime.now(timezone.utc)
                session.commit()

                logger.info(f"⏹️ Stopped monitoring fixture {fixture_id}")
```

---

## 📱 5. Comandos de Telegram

### `src/notifications/telegram_handlers.py` (agregar handlers)

```python
"""Add live match handlers"""

async def handle_live_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra partidos en vivo siendo monitoreados"""
    user_id = str(update.effective_user.id)

    with db_manager.get_session() as session:
        monitored = session.query(MonitoredMatch).join(
            Fixture
        ).filter(
            MonitoredMatch.is_active == True
        ).all()

        if not monitored:
            await update.message.reply_text(
                "🔴 No hay partidos siendo monitoreados actualmente.\\n\\n"
                "Usa /monitor para comenzar a seguir un partido en vivo."
            )
            return

        # Construir mensaje con lista de partidos
        message = "🔴 **PARTIDOS EN VIVO MONITOREADOS**\\n\\n"

        for m in monitored:
            fixture = m.fixture
            # Obtener último estado
            last_state = session.query(LiveMatchState).filter(
                LiveMatchState.fixture_id == m.fixture_id
            ).order_by(LiveMatchState.snapshot_number.desc()).first()

            if last_state:
                message += (
                    f"⚽ {fixture.home_team} vs {fixture.away_team}\\n"
                    f"   Score: {last_state.score_home}-{last_state.score_away} "
                    f"({last_state.minute}')\\n"
                    f"   Probabilidades: {last_state.live_home_prob:.1%} / "
                    f"{last_state.live_draw_prob:.1%} / "
                    f"{last_state.live_away_prob:.1%}\\n\\n"
                )

        await update.message.reply_text(message, parse_mode="Markdown")


async def handle_monitor_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comienza a monitorear un partido"""
    if not context.args:
        await update.message.reply_text(
            "❌ Uso: /monitor <fixture_id>\\n\\n"
            "Ejemplo: /monitor 12345"
        )
        return

    fixture_id = int(context.args[0])
    user_id = str(update.effective_user.id)

    # Verificar que el partido existe y está en vivo
    api = APIFootballClient()
    fixture_data = api.get_fixture_live_state(fixture_id)

    if not fixture_data:
        await update.message.reply_text("❌ Partido no encontrado")
        return

    status = fixture_data.get("fixture", {}).get("status", {}).get("short")

    if status not in ["1H", "HT", "2H", "ET", "LIVE"]:
        await update.message.reply_text(
            f"❌ El partido no está en vivo actualmente (Status: {status})"
        )
        return

    # Iniciar monitoreo
    monitor = context.bot_data.get("live_monitor")
    await monitor.start_monitoring(fixture_id, user_id)

    teams = fixture_data.get("teams", {})
    await update.message.reply_text(
        f"✅ Ahora monitoreando:\\n\\n"
        f"⚽ {teams.get('home', {}).get('name')} vs "
        f"{teams.get('away', {}).get('name')}\\n\\n"
        f"Recibirás actualizaciones cada 5 minutos."
    )
```

---

## 🔧 6. Configuración

### `src/utils/config.py` (agregar variables)

```python
# Live Match Monitoring
LIVE_UPDATE_INTERVAL: int = Field(
    default=5,
    ge=1,
    le=30,
    description="Interval in minutes for live match updates"
)
MAX_LIVE_MATCHES: int = Field(
    default=5,
    ge=1,
    le=20,
    description="Maximum number of matches to monitor simultaneously"
)
LIVE_PROB_CHANGE_THRESHOLD: float = Field(
    default=0.15,
    ge=0.05,
    le=0.50,
    description="Minimum probability change to trigger notification"
)
```

---

## 🗃️ 7. Migración de Base de Datos

### Script de migración (ejecutar una vez)

```python
"""Migration script: Add live match tables"""
from src.database import db_manager, Base

def run_migration():
    """Crea las nuevas tablas para live matches"""
    print("Creating live match tables...")

    engine = db_manager.get_engine()

    # Importar modelos para que SQLAlchemy los conozca
    from src.database.models import LiveMatchState, MonitoredMatch

    # Crear solo las nuevas tablas (no afecta las existentes)
    Base.metadata.create_all(
        engine,
        tables=[LiveMatchState.__table__, MonitoredMatch.__table__]
    )

    print("✅ Migration completed successfully")

if __name__ == "__main__":
    run_migration()
```

---

## 🚀 Uso

### Ejemplo de integración en main.py

```python
from src.services.live_match_monitor import LiveMatchMonitor

class FootballBettingBot:
    def __init__(self):
        # ... existing code ...
        self.live_monitor = LiveMatchMonitor()

    async def startup(self):
        # ... existing startup code ...

        # Iniciar monitor de partidos en vivo
        await self.live_monitor.start()
        logger.info("✅ Live match monitor started")

    async def shutdown(self):
        # Detener monitor
        if self.live_monitor:
            await self.live_monitor.stop()

        # ... existing shutdown code ...
```

---

**Siguiente paso**: Implementar estos archivos uno por uno según el plan de fases del documento de investigación.
