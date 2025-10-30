"""Telegram bot command handlers"""
import asyncio
from typing import TYPE_CHECKING
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from ..utils.config import Config
from ..utils.logger import setup_logger
from .message_formatter import MessageFormatter
from .telegram_menu import TelegramMenu
from .telegram_handlers import TelegramHandlers

if TYPE_CHECKING:
    from ..services import BotService

logger = setup_logger(__name__)


class TelegramCommandBot:
    """Handles Telegram bot commands"""

    def __init__(self, bot_service: "BotService"):
        """Initialize command bot"""
        self.bot_service = bot_service
        self.formatter = MessageFormatter()
        self.menu = TelegramMenu(bot_service)
        self.handlers = TelegramHandlers(bot_service)
        self.application = None

        if not Config.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not configured")

        logger.debug("Telegram command bot initialized")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - Show main menu"""
        # Send persistent keyboard
        await update.message.reply_text(
            "🎮 Menú activado",
            reply_markup=self.menu.get_persistent_keyboard()
        )

        # Show sports menu
        message = """
🤖 <b>Bienvenido al Bot de Análisis Deportivo</b>

Este bot te ayuda a analizar partidos y detectar oportunidades usando análisis estadístico puro (Distribución de Poisson).

🏠 <b>Usa el botón "Menú Principal" para navegar</b>

Selecciona un deporte para comenzar:
"""
        await update.message.reply_text(
            message,
            parse_mode="HTML",
            reply_markup=self.menu.get_sports_menu()
        )
        logger.info(f"User {update.effective_user.id} started bot")

    async def menu_button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle persistent menu button press"""
        if update.message.text == "🏠 Menú Principal":
            await self.menu.show_sports_menu(update, context)
            logger.info(f"User {update.effective_user.id} opened main menu")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        # Get current status
        enabled_leagues = Config.ENABLED_LEAGUES

        message = f"""
📊 <b>Estado del Bot</b>

✅ Bot activo y funcionando

<b>Configuración:</b>
• Ligas: {len(enabled_leagues)} monitoreadas
• Intervalo: {Config.CHECK_INTERVAL} minutos
• Alerta: {Config.ALERT_TIME_MINUTES} min antes del partido
• Edge mínimo: {Config.MINIMUM_EDGE * 100}%

<b>Próximo análisis:</b>
En los próximos {Config.CHECK_INTERVAL} minutos

Usa /partidos para ver partidos próximos.
"""
        await update.message.reply_text(message, parse_mode="HTML")
        logger.info(f"User {update.effective_user.id} requested status")

    async def partidos_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /partidos command"""
        await update.message.reply_text("🔍 Buscando partidos de la semana (Lunes-Domingo)...")

        try:
            # Get upcoming fixtures (7 days = 168 hours) - uses BD cache
            fixtures = await asyncio.to_thread(
                self.bot_service.fixtures_service.get_upcoming_fixtures,
                hours_ahead=168,
                force_refresh=False
            )

            if not fixtures:
                message = """
😕 <b>No hay partidos próximos</b>

No se encontraron partidos en la próxima semana (Lun-Dom) para las ligas configuradas.

Usa /ligas para ver qué ligas estamos monitoreando.
"""
                await update.message.reply_text(message, parse_mode="HTML")
                return

            # Format fixtures
            message = f"⚽ <b>Partidos de la Semana</b> ({len(fixtures)} encontrados)\n\n"

            for fixture in fixtures[:20]:  # Show max 20
                fixture_info = fixture.get("fixture", {})
                teams = fixture.get("teams", {})
                league = fixture.get("league", {})

                date_str = fixture_info.get("date", "")[:16].replace("T", " ")
                home_team = teams.get("home", {}).get("name", "")
                away_team = teams.get("away", {}).get("name", "")
                league_name = league.get("name", "")

                message += f"🏆 {league_name}\n"
                message += f"📅 {date_str}\n"
                message += f"⚽ {home_team} vs {away_team}\n\n"

            if len(fixtures) > 20:
                message += f"... y {len(fixtures) - 20} partidos más\n"

            await update.message.reply_text(message, parse_mode="HTML")
            logger.info(f"User {update.effective_user.id} requested fixtures")

        except Exception as e:
            logger.error(f"Error getting fixtures: {e}")
            await update.message.reply_text(
                "❌ Error al obtener partidos. Intenta de nuevo más tarde.",
                parse_mode="HTML"
            )

    async def ligas_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ligas command"""
        from ..utils.config import LEAGUE_CONFIG

        enabled_leagues = Config.ENABLED_LEAGUES

        message = "🏆 <b>Ligas Monitoreadas</b>\n\n"

        for league_id in enabled_leagues:
            league_info = LEAGUE_CONFIG.get(league_id, {})
            name = league_info.get("name", f"Liga {league_id}")
            country = league_info.get("country", "Unknown")
            message += f"• {name} ({country})\n"

        message += f"\n<b>Total:</b> {len(enabled_leagues)} ligas\n"
        message += "\nEl bot analiza partidos de estas ligas y te envía alertas cuando detecta oportunidades."

        await update.message.reply_text(message, parse_mode="HTML")
        logger.info(f"User {update.effective_user.id} requested leagues")

    async def analizar_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analizar command"""
        await update.message.reply_text("🔍 Analizando partidos de la semana con value bets...")

        try:
            # Get upcoming fixtures (7 days = 168 hours) - uses BD cache
            fixtures = await asyncio.to_thread(
                self.bot_service.fixtures_service.get_upcoming_fixtures,
                hours_ahead=168,
                force_refresh=False
            )

            if not fixtures:
                await update.message.reply_text(
                    "😕 No hay partidos para analizar en la próxima semana.",
                    parse_mode="HTML"
                )
                return

            # Analyze each fixture
            analyzed_count = 0
            value_bets_found = 0

            for fixture in fixtures[:10]:  # Analyze first 10 fixtures
                try:
                    fixture_info = fixture.get("fixture", {})
                    teams = fixture.get("teams", {})
                    fixture_id = fixture_info.get("id")

                    home_team = teams.get("home", {}).get("name", "")
                    away_team = teams.get("away", {}).get("name", "")

                    # Send analyzing message
                    await update.message.reply_text(
                        f"📊 Analizando: {home_team} vs {away_team}...",
                        parse_mode="HTML"
                    )

                    # Perform analysis
                    analysis = await asyncio.to_thread(
                        self.bot_service.analyze_fixture,
                        fixture
                    )

                    if analysis and analysis.get("has_value"):
                        value_bets_found += 1
                        # Format detailed analysis
                        message = self._format_detailed_analysis(fixture, analysis)
                        await update.message.reply_text(message, parse_mode="HTML")
                    else:
                        # Just show basic analysis
                        message = self._format_basic_analysis(fixture, analysis)
                        await update.message.reply_text(message, parse_mode="HTML")

                    analyzed_count += 1

                except Exception as e:
                    logger.error(f"Error analyzing fixture {fixture_id}: {e}")
                    continue

            # Summary
            summary = f"""
📈 <b>Análisis Completado</b>

✅ Partidos analizados: {analyzed_count}
💰 Value bets encontrados: {value_bets_found}

{f'¡Encontramos {value_bets_found} oportunidades!' if value_bets_found > 0 else 'No se detectaron value bets en este momento.'}
"""
            await update.message.reply_text(summary, parse_mode="HTML")
            logger.info(f"User {update.effective_user.id} analyzed {analyzed_count} fixtures")

        except Exception as e:
            logger.error(f"Error in analyze command: {e}")
            await update.message.reply_text(
                "❌ Error al analizar partidos. Intenta de nuevo más tarde.",
                parse_mode="HTML"
            )

    def _format_detailed_analysis(self, fixture: dict, analysis: dict) -> str:
        """Format detailed analysis with value bet"""
        fixture_info = fixture.get("fixture", {})
        teams = fixture.get("teams", {})
        league = fixture.get("league", {})

        home_team = teams.get("home", {}).get("name", "")
        away_team = teams.get("away", {}).get("name", "")
        league_name = league.get("name", "")
        date_str = fixture_info.get("date", "")[:16].replace("T", " ")

        prob = analysis.get("probabilities", {})
        stats = analysis.get("statistics", {})
        value = analysis.get("value_bet", {})

        message = f"""
⚽ <b>OPORTUNIDAD DETECTADA</b>

🏆 {league_name}
📅 {home_team} vs {away_team}
🕐 {date_str}

━━━━━━━━━━━━━━━━━━━━━━

📊 <b>PROBABILIDADES CALCULADAS</b>
• Local (1): {prob.get('home', 0)*100:.1f}%
• Empate (X): {prob.get('draw', 0)*100:.1f}%
• Visitante (2): {prob.get('away', 0)*100:.1f}%

⚽ <b>GOLES ESPERADOS</b>
• {home_team}: {stats.get('expected_goals_home', 0):.2f}
• {away_team}: {stats.get('expected_goals_away', 0):.2f}

💰 <b>VALUE BET</b>
• Resultado: {value.get('outcome', 'N/A')}
• Edge: +{value.get('edge', 0)*100:.1f}%
• Confianza: {'⭐' * value.get('confidence', 3)}

📈 <b>TENDENCIAS</b>
• Forma local (últimos 5): {stats.get('home_form', 'N/A')}
• Forma visitante (últimos 5): {stats.get('away_form', 'N/A')}

💡 <b>RECOMENDACIÓN</b>
Stake sugerido: {value.get('suggested_stake', 0)*100:.0f}% del bankroll

⚠️ Análisis estadístico - Apuesta responsable
"""
        return message

    def _format_basic_analysis(self, fixture: dict, analysis: dict) -> str:
        """Format basic analysis without value bet"""
        fixture_info = fixture.get("fixture", {})
        teams = fixture.get("teams", {})

        home_team = teams.get("home", {}).get("name", "")
        away_team = teams.get("away", {}).get("name", "")

        if not analysis:
            return f"❌ {home_team} vs {away_team}: No hay suficientes datos para análisis"

        prob = analysis.get("probabilities", {})
        stats = analysis.get("statistics", {})

        message = f"""
📊 <b>{home_team} vs {away_team}</b>

Probabilidades:
• Local: {prob.get('home', 0)*100:.1f}%
• Empate: {prob.get('draw', 0)*100:.1f}%
• Visitante: {prob.get('away', 0)*100:.1f}%

Goles esperados:
• {home_team}: {stats.get('expected_goals_home', 0):.2f}
• {away_team}: {stats.get('expected_goals_away', 0):.2f}

ℹ️ No se detectó value bet (edge < 5%)
"""
        return message

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        message = """
❓ <b>Ayuda - Bot de Apuestas</b>

<b>¿Qué hace este bot?</b>
Analiza partidos de fútbol usando estadísticas reales y detecta oportunidades de value bets (ventaja > 5%).

<b>Comandos:</b>

/start - Iniciar el bot
/status - Ver estado actual
/partidos - Ver partidos de la semana (Lun-Dom)
/analizar - Analizar partidos con tendencias y value bets
/ligas - Ver ligas monitoreadas
/help - Esta ayuda

<b>¿Cómo funciona?</b>

1️⃣ El bot revisa partidos cada 30 minutos
2️⃣ Analiza estadísticas usando distribución de Poisson
3️⃣ Compara probabilidades vs cuotas de casas
4️⃣ Te envía alerta 1 hora antes si detecta value bet

<b>Análisis estadístico puro - Sin IA</b>

⚠️ <b>Disclaimer:</b> Este es un análisis estadístico con fines educativos. Apuesta responsablemente.
"""
        await update.message.reply_text(message, parse_mode="HTML")
        logger.info(f"User {update.effective_user.id} requested help")

    async def start(self):
        """Start the command bot"""
        try:
            # Create application
            self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

            # Add command handlers
            self.application.add_handler(CommandHandler("start", self.start_command))

            # Add callback query handler for inline buttons
            self.application.add_handler(CallbackQueryHandler(self.handlers.handle_callback))

            # Add message handler for persistent keyboard button
            self.application.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.menu_button_handler
            ))

            # Start polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()

            logger.info("Telegram command bot started")

        except Exception as e:
            logger.error(f"Failed to start command bot: {e}")
            raise

    async def stop(self):
        """Stop the command bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram command bot stopped")
