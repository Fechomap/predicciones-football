"""Telegram callback handlers for inline buttons"""
import asyncio
from typing import TYPE_CHECKING
from telegram import Update
from telegram.ext import ContextTypes

from ..utils.logger import setup_logger
from ..utils.cache import fixtures_cache
from .telegram_menu import TelegramMenu
from .message_formatter import MessageFormatter

if TYPE_CHECKING:
    from ..services import BotService

logger = setup_logger(__name__)


async def safe_edit_message(query, text: str, **kwargs):
    """
    Safely edit Telegram message, handling 'Message is not modified' error

    This error occurs when user clicks same button twice (no content change).
    We handle it gracefully to avoid polluting logs.

    Args:
        query: CallbackQuery object
        text: New message text
        **kwargs: Additional arguments for edit_message_text
    """
    try:
        await query.edit_message_text(text, **kwargs)
    except Exception as e:
        if "message is not modified" in str(e).lower():
            logger.debug("Message content unchanged, skipping edit")
            await query.answer()  # Just acknowledge the button press
        else:
            # Re-raise other errors
            raise


class TelegramHandlers:
    """Handles all callback queries from inline buttons"""

    def __init__(self, bot_service: "BotService"):
        """Initialize handlers"""
        self.bot_service = bot_service
        self.menu = TelegramMenu(bot_service)
        logger.debug("Telegram handlers initialized")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Main callback handler for all inline button presses

        Routes callbacks to appropriate handlers based on callback_data
        """
        query = update.callback_query
        await query.answer()  # Acknowledge the button press

        callback_data = query.data
        logger.info(f"Callback received: {callback_data} from user {update.effective_user.id}")

        try:
            # Route to appropriate handler
            if callback_data.startswith("sport_"):
                await self._handle_sport_selection(update, context, callback_data)

            elif callback_data.startswith("league_"):
                await self._handle_league_selection(update, context, callback_data)

            elif callback_data.startswith("leagues_page_"):
                await self._handle_leagues_pagination(update, context, callback_data)

            elif callback_data.startswith("fixture_"):
                await self._handle_fixture_selection(update, context, callback_data)

            elif callback_data.startswith("analyze_"):
                await self._handle_analyze_fixture(update, context, callback_data)

            elif callback_data.startswith("refresh_league_"):
                await self._handle_refresh_league(update, context, callback_data)

            elif callback_data.startswith("refresh_"):
                await self._handle_refresh_fixture(update, context, callback_data)

            elif callback_data == "back_to_sports":
                await self.menu.show_sports_menu(update, context)

            elif callback_data == "back_to_leagues":
                sport_id = context.user_data.get('current_sport', 'football')
                await self.menu.show_leagues_menu(update, context, sport_id)

            elif callback_data == "back_to_fixtures":
                league_id = context.user_data.get('current_league')
                if league_id:
                    await self.menu.show_fixtures_menu(update, context, league_id)

            elif callback_data == "coming_soon":
                await query.answer("🚧 Próximamente disponible", show_alert=True)

            elif callback_data == "no_action":
                await query.answer()

            else:
                logger.warning(f"Unknown callback: {callback_data}")
                await query.answer("❌ Acción no reconocida", show_alert=True)

        except Exception as e:
            logger.error(f"Error handling callback {callback_data}: {e}")
            await query.answer("❌ Error procesando acción", show_alert=True)

    async def _handle_sport_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Handle sport selection"""
        sport_id = callback_data.replace("sport_", "")
        await self.menu.show_leagues_menu(update, context, sport_id)

    async def _handle_league_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Handle league selection"""
        league_id = int(callback_data.replace("league_", ""))
        await self.menu.show_fixtures_menu(update, context, league_id)

    async def _handle_leagues_pagination(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Handle league pagination"""
        page = int(callback_data.replace("leagues_page_", ""))
        sport_id = context.user_data.get('current_sport', 'football')
        await self.menu.show_leagues_menu(update, context, sport_id, page)

    async def _handle_fixture_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Handle fixture selection"""
        fixture_id = int(callback_data.replace("fixture_", ""))
        await self.menu.show_fixture_details(update, context, fixture_id)

    async def _handle_analyze_fixture(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Handle analyze fixture request"""
        fixture_id = int(callback_data.replace("analyze_", ""))

        await safe_edit_message(
            update.callback_query,
            "📊 Analizando partido...\n\nEsto puede tomar unos segundos.",
            parse_mode="HTML"
        )

        try:
            # Get fixtures from BD (fast)
            fixtures = await asyncio.to_thread(
                self.bot_service.fixtures_service.get_upcoming_fixtures,
                hours_ahead=168,
                force_refresh=False
            )

            # Find the specific fixture
            fixture = next((f for f in fixtures if f.get("fixture", {}).get("id") == fixture_id), None)

            if not fixture:
                await safe_edit_message(
                    update.callback_query,
                    "❌ Partido no encontrado.",
                    parse_mode="HTML"
                )
                return

            # Perform analysis
            analysis = await asyncio.to_thread(
                self.bot_service.analyze_fixture,
                fixture
            )

            if not analysis:
                await safe_edit_message(
                    update.callback_query,
                    "❌ No se pudo analizar el partido.\n\n"
                    "<i>Posibles causas:</i>\n"
                    "• No hay estadísticas disponibles para los equipos\n"
                    "• Error temporal en la API\n"
                    "• El partido fue cancelado o pospuesto\n\n"
                    "Por favor, intenta más tarde o usa el botón 🔄 Refrescar.",
                    parse_mode="HTML"
                )
                return

            # Format analysis message
            message = self._format_analysis(fixture, analysis)

            # Send analysis
            await safe_edit_message(
                update.callback_query,
                message,
                parse_mode="HTML"
            )

            # Send action buttons in a new message
            await update.callback_query.message.reply_text(
                "¿Qué deseas hacer?",
                reply_markup=self.menu.get_fixture_actions_menu(fixture_id)
            )

            logger.info(f"Analysis completed for fixture {fixture_id}")

        except Exception as e:
            logger.error(f"Error analyzing fixture {fixture_id}: {e}")
            await safe_edit_message(
                update.callback_query,
                f"❌ Error al analizar: {str(e)}",
                parse_mode="HTML"
            )

    async def _handle_refresh_league(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Handle refresh league fixtures (new API call)"""
        league_id = int(callback_data.replace("refresh_league_", ""))

        await safe_edit_message(
            update.callback_query,
            "🔄 <b>Consultando API...</b>\n\nObteniendo partidos actualizados de todas las ligas.",
            parse_mode="HTML"
        )

        # Force refresh from API
        await asyncio.to_thread(
            self.bot_service.fixtures_service.get_upcoming_fixtures,
            hours_ahead=168,
            force_refresh=True  # This forces new API call
        )

        # Show updated fixtures menu
        await self.menu.show_fixtures_menu(update, context, league_id)

    async def _handle_refresh_fixture(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Handle refresh fixture data (new API call)"""
        fixture_id = int(callback_data.replace("refresh_", ""))

        await update.callback_query.answer("🔄 Consultando API para datos frescos...", show_alert=True)

        # Force refresh from API
        await asyncio.to_thread(
            self.bot_service.fixtures_service.get_upcoming_fixtures,
            hours_ahead=168,
            force_refresh=True  # This forces new API call
        )

        # Re-analyze with fresh data
        await self._handle_analyze_fixture(update, context, f"analyze_{fixture_id}")

    def _format_analysis(self, fixture: dict, analysis: dict) -> str:
        """Format analysis results into a message"""
        import html

        fixture_info = fixture.get("fixture", {})
        teams = fixture.get("teams", {})
        league = fixture.get("league", {})

        # Escape HTML to prevent parsing errors
        home_team = html.escape(teams.get("home", {}).get("name", ""))
        away_team = html.escape(teams.get("away", {}).get("name", ""))
        league_name = html.escape(league.get("name", ""))
        date_str = fixture_info.get("date", "")[:16].replace("T", " ")

        our_pred = analysis.get("our_prediction", {})
        api_pred = analysis.get("api_prediction", {})
        stats = analysis.get("statistics", {})
        goal_ranges = analysis.get("goal_ranges", {})
        value = analysis.get("value_bet")

        # Base message - ALWAYS show both predictions
        message = f"""
⚽ <b>ANÁLISIS DEL PARTIDO</b>

🏆 {league_name}
📅 {home_team} vs {away_team}
🕐 {date_str}

━━━━━━━━━━━━━━━━━━━━━━

🤖 <b>PREDICCIÓN API-FOOTBALL</b>
• Local (1): {(api_pred.get('home') or 0)*100:.1f}%
• Empate (X): {(api_pred.get('draw') or 0)*100:.1f}%
• Visitante (2): {(api_pred.get('away') or 0)*100:.1f}%
{f"• Ganador sugerido: {api_pred.get('winner', 'N/A')}" if api_pred.get('winner') else ""}

🧮 <b>NUESTRA PREDICCIÓN (Poisson)</b>
• Local (1): {our_pred.get('home', 0)*100:.1f}%
• Empate (X): {our_pred.get('draw', 0)*100:.1f}%
• Visitante (2): {our_pred.get('away', 0)*100:.1f}%

📊 <b>COMPARACIÓN</b>
• Diferencia Local: {abs((our_pred.get('home', 0) - (api_pred.get('home') or 0)) * 100):.1f}%
• Diferencia Empate: {abs((our_pred.get('draw', 0) - (api_pred.get('draw') or 0)) * 100):.1f}%
• Diferencia Visitante: {abs((our_pred.get('away', 0) - (api_pred.get('away') or 0)) * 100):.1f}%

━━━━━━━━━━━━━━━━━━━━━━

⚽ <b>GOLES ESPERADOS</b>
• {home_team}: {stats.get('expected_goals_home', 0):.2f}
• {away_team}: {stats.get('expected_goals_away', 0):.2f}

🥅 <b>PROBABILIDAD DE GOLES TOTALES</b>
• 0-1 Goles: {goal_ranges.get('0-1', 0) * 100:.1f}%
• 2-3 Goles: {goal_ranges.get('2-3', 0) * 100:.1f}%
• 4+ Goles: {goal_ranges.get('4+', 0) * 100:.1f}%

📈 <b>FORMA RECIENTE</b> (últimos 5 partidos)
• {home_team}: {MessageFormatter._format_form_string(stats.get('home_form', 'N/A'))}
• {away_team}: {MessageFormatter._format_form_string(stats.get('away_form', 'N/A'))}

📊 <b>PARTIDOS JUGADOS</b>
• {home_team} (casa): {stats.get('home_matches', 0)} partidos
• {away_team} (visita): {stats.get('away_matches', 0)} partidos
"""

        # Add value bet section if detected
        if analysis.get("odds_unavailable"):
            # No odds available - show warning
            message += """
━━━━━━━━━━━━━━━━━━━━━━

⚠️ <b>CUOTAS NO DISPONIBLES</b>

No se pudieron obtener cuotas de mercado para este partido.

<i>Posibles razones:</i>
• El partido está muy lejos en el futuro
• Las casas de apuestas aún no publicaron cuotas
• Error temporal en la API

El análisis estadístico (arriba) sigue siendo válido.
Intenta de nuevo más cerca del partido.
"""
        elif analysis.get("has_value") and value:
            confidence_stars = "⭐" * min(value.get('confidence', 3), 5)
            message += f"""
━━━━━━━━━━━━━━━━━━━━━━

💰 <b>VALUE BET DETECTADO</b>
<i>(Basado en nuestra predicción Poisson)</i>

• Resultado: {html.escape(str(value.get('outcome', 'N/A')))}
• Edge: +{value.get('edge', 0)*100:.1f}%
• Confianza: {confidence_stars}

💡 <b>RECOMENDACIÓN</b>
Stake sugerido: {value.get('suggested_stake', 0)*100:.0f}% del bankroll
"""
        else:
            message += """
━━━━━━━━━━━━━━━━━━━━━━

ℹ️ <b>No se detectó value bet</b>
(Edge menor a 5%)
"""

        message += "\n\n⚠️ Análisis estadístico - Apuesta responsable"

        return message
