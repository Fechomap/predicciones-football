"""Telegram bot menu system with inline keyboards"""
from typing import TYPE_CHECKING, Optional, List, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler

from ..utils.config import Config, LEAGUE_CONFIG
from ..utils.logger import setup_logger
from ..utils.cache import fixtures_cache

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


class TelegramMenu:
    """Handles menu navigation with inline keyboards"""

    # Available sports (top 10 for betting)
    SPORTS = [
        {"name": "⚽ Fútbol", "id": "football"},
        {"name": "🏀 Básquetbol", "id": "basketball"},
        {"name": "⚾ Béisbol", "id": "baseball"},
        {"name": "🎾 Tenis", "id": "tennis"},
        {"name": "🏈 Fútbol Americano", "id": "american_football"},
        {"name": "🏒 Hockey", "id": "hockey"},
        {"name": "🏐 Voleibol", "id": "volleyball"},
        {"name": "🏉 Rugby", "id": "rugby"},
        {"name": "🏏 Cricket", "id": "cricket"},
        {"name": "🥊 Boxeo", "id": "boxing"},
    ]

    # Top leagues (priority order)
    TOP_LEAGUES = [262, 39, 140, 78, 135, 61]  # Liga MX, Premier, La Liga, Bundesliga, Serie A, Ligue 1

    def __init__(self, bot_service: "BotService"):
        """Initialize menu"""
        self.bot_service = bot_service
        logger.debug("Telegram menu initialized")

    @staticmethod
    def get_persistent_keyboard() -> ReplyKeyboardMarkup:
        """Get persistent keyboard with Home button"""
        keyboard = [[KeyboardButton("🏠 Menú Principal")]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

    def get_sports_menu(self) -> InlineKeyboardMarkup:
        """Get sports selection menu"""
        keyboard = []
        row = []

        for i, sport in enumerate(self.SPORTS):
            row.append(InlineKeyboardButton(sport["name"], callback_data=f"sport_{sport['id']}"))

            # 2 buttons per row
            if len(row) == 2:
                keyboard.append(row)
                row = []

        # Add remaining button if odd number
        if row:
            keyboard.append(row)

        return InlineKeyboardMarkup(keyboard)

    def get_leagues_menu(self, sport_id: str, page: int = 0) -> InlineKeyboardMarkup:
        """
        Get leagues menu with pagination

        Args:
            sport_id: Sport identifier
            page: Page number (0-indexed)

        Returns:
            InlineKeyboardMarkup with leagues
        """
        # For now, only football is implemented
        if sport_id != "football":
            keyboard = [[InlineKeyboardButton("🚧 Próximamente", callback_data="coming_soon")]]
            keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_to_sports")])
            return InlineKeyboardMarkup(keyboard)

        # Get all available leagues from config
        all_leagues = list(LEAGUE_CONFIG.keys())

        # Sort: top leagues first, then others
        top_leagues = [lid for lid in self.TOP_LEAGUES if lid in all_leagues]
        other_leagues = [lid for lid in all_leagues if lid not in self.TOP_LEAGUES]
        sorted_leagues = top_leagues + other_leagues

        # Pagination: 6 leagues per page
        per_page = 6
        start_idx = page * per_page
        end_idx = start_idx + per_page
        page_leagues = sorted_leagues[start_idx:end_idx]

        keyboard = []

        # Add league buttons (2 per row)
        row = []
        for league_id in page_leagues:
            league_info = LEAGUE_CONFIG[league_id]
            emoji = league_info.get("emoji", "🏆")
            name = league_info.get("name", f"League {league_id}")

            row.append(InlineKeyboardButton(
                f"{emoji} {name}",
                callback_data=f"league_{league_id}"
            ))

            if len(row) == 2:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        # Navigation buttons
        nav_row = []

        # Previous page
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"leagues_page_{page-1}"))

        # Next page
        if end_idx < len(sorted_leagues):
            nav_row.append(InlineKeyboardButton("Siguiente ➡️", callback_data=f"leagues_page_{page+1}"))

        if nav_row:
            keyboard.append(nav_row)

        # Back button
        keyboard.append([InlineKeyboardButton("🔙 Volver a Deportes", callback_data="back_to_sports")])

        return InlineKeyboardMarkup(keyboard)

    async def get_fixtures_menu(self, league_id: int, force_refresh: bool = False) -> InlineKeyboardMarkup:
        """
        Get fixtures menu for a specific league

        Args:
            league_id: League ID
            force_refresh: Force API call even if BD has data

        Returns:
            InlineKeyboardMarkup with fixtures
        """
        import asyncio

        # Use BD-first approach via fixtures_service
        fixtures = await asyncio.to_thread(
            self.bot_service.fixtures_service.get_upcoming_fixtures,
            hours_ahead=168,
            force_refresh=force_refresh
        )

        # Filter by league
        league_fixtures = [f for f in fixtures if f.get("league", {}).get("id") == league_id]

        keyboard = []

        if not league_fixtures:
            keyboard.append([InlineKeyboardButton("😕 No hay partidos esta semana", callback_data="no_fixtures")])
        else:
            # Show up to 15 fixtures
            for i, fixture in enumerate(league_fixtures[:15], 1):
                fixture_info = fixture.get("fixture", {})
                teams = fixture.get("teams", {})

                fixture_id = fixture_info.get("id")
                date = fixture_info.get("date", "")[:10]  # YYYY-MM-DD
                time = fixture_info.get("date", "")[11:16]  # HH:MM

                home = teams.get("home", {}).get("name", "")[:15]  # Truncate long names
                away = teams.get("away", {}).get("name", "")[:15]

                button_text = f"{i}. {home} vs {away} - {date} {time}"

                keyboard.append([InlineKeyboardButton(
                    button_text,
                    callback_data=f"fixture_{fixture_id}"
                )])

            if len(league_fixtures) > 15:
                keyboard.append([InlineKeyboardButton(
                    f"... y {len(league_fixtures) - 15} partidos más",
                    callback_data="no_action"
                )])

        # Refresh and navigation buttons
        keyboard.append([InlineKeyboardButton("🔄 Refrescar Partidos (Consultar API)", callback_data=f"refresh_league_{league_id}")])
        keyboard.append([InlineKeyboardButton("🔙 Volver a Ligas", callback_data="back_to_leagues")])

        return InlineKeyboardMarkup(keyboard)

    def get_fixture_actions_menu(self, fixture_id: int) -> InlineKeyboardMarkup:
        """
        Get action menu for a specific fixture

        Args:
            fixture_id: Fixture ID

        Returns:
            InlineKeyboardMarkup with actions
        """
        keyboard = [
            [InlineKeyboardButton("📊 Analizar Partido", callback_data=f"analyze_{fixture_id}")],
            [InlineKeyboardButton("🔄 Actualizar Datos", callback_data=f"refresh_{fixture_id}")],
            [InlineKeyboardButton("🔙 Volver a Partidos", callback_data="back_to_fixtures")],
            [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_sports")]
        ]

        return InlineKeyboardMarkup(keyboard)

    async def show_sports_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show sports selection menu"""
        message = """
🏠 <b>Menú Principal</b>

Selecciona el deporte que deseas consultar:
"""

        if update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                parse_mode="HTML",
                reply_markup=self.get_sports_menu()
            )
        else:
            await update.message.reply_text(
                message,
                parse_mode="HTML",
                reply_markup=self.get_sports_menu()
            )

    async def show_leagues_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, sport_id: str, page: int = 0):
        """Show leagues menu"""
        sport_name = next((s["name"] for s in self.SPORTS if s["id"] == sport_id), "Deporte")

        message = f"""
{sport_name}

Selecciona la liga que deseas consultar:
"""

        # Store current sport in context
        context.user_data['current_sport'] = sport_id

        await update.callback_query.edit_message_text(
            message,
            parse_mode="HTML",
            reply_markup=self.get_leagues_menu(sport_id, page)
        )

    async def show_fixtures_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, league_id: int):
        """Show fixtures menu"""
        league_info = LEAGUE_CONFIG.get(league_id, {})
        league_name = league_info.get("name", f"Liga {league_id}")
        emoji = league_info.get("emoji", "🏆")

        await update.callback_query.edit_message_text(
            f"🔍 Cargando partidos de {emoji} {league_name}...",
            parse_mode="HTML"
        )

        # Store current league in context
        context.user_data['current_league'] = league_id

        message = f"""
{emoji} <b>{league_name}</b>

📅 Partidos de la Semana:
"""

        markup = await self.get_fixtures_menu(league_id)

        await update.callback_query.edit_message_text(
            message,
            parse_mode="HTML",
            reply_markup=markup
        )

    async def show_fixture_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE, fixture_id: int):
        """Show fixture details and actions"""
        import asyncio

        # Get all fixtures (uses BD cache)
        fixtures = await asyncio.to_thread(
            self.bot_service.fixtures_service.get_upcoming_fixtures,
            hours_ahead=168,
            force_refresh=False
        )

        # Find the specific fixture
        fixture = next((f for f in fixtures if f.get("fixture", {}).get("id") == fixture_id), None)

        if not fixture:
            await update.callback_query.answer("❌ Partido no encontrado", show_alert=True)
            return

        # Store current fixture in context
        context.user_data['current_fixture'] = fixture_id

        # Format fixture details
        fixture_info = fixture.get("fixture", {})
        teams = fixture.get("teams", {})
        league = fixture.get("league", {})

        date = fixture_info.get("date", "")[:16].replace("T", " ")
        home = teams.get("home", {}).get("name", "")
        away = teams.get("away", {}).get("name", "")
        league_name = league.get("name", "")
        venue = fixture_info.get("venue", {}).get("name", "")

        message = f"""
🏆 <b>{league_name}</b>

⚽ <b>{home} vs {away}</b>

📅 Fecha: {date}
🏟️ Estadio: {venue}

¿Qué deseas hacer?
"""

        await safe_edit_message(
            update.callback_query,
            message,
            parse_mode="HTML",
            reply_markup=self.get_fixture_actions_menu(fixture_id)
        )
