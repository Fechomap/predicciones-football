"""Configuration management"""
import os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""

    # API-Football
    RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
    RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "api-football-v1.p.rapidapi.com")

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Bot Configuration
    ALERT_TIME_MINUTES = int(os.getenv("ALERT_TIME_MINUTES", "60"))
    MINIMUM_EDGE = float(os.getenv("MINIMUM_EDGE", "0.05"))
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))
    MIN_CONFIDENCE = int(os.getenv("MIN_CONFIDENCE", "3"))
    MAX_ALERTS_PER_DAY = int(os.getenv("MAX_ALERTS_PER_DAY", "10"))

    # Bankroll Management
    BANKROLL = float(os.getenv("BANKROLL", "1000"))  # Default $1000 bankroll

    # Leagues
    ENABLED_LEAGUES: List[int] = [
        int(league_id.strip())
        for league_id in os.getenv("ENABLED_LEAGUES", "262").split(",")
    ]

    # Railway
    RAILWAY_ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "development")
    PORT = int(os.getenv("PORT", "8000"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required = [
            ("RAPIDAPI_KEY", cls.RAPIDAPI_KEY),
            ("TELEGRAM_BOT_TOKEN", cls.TELEGRAM_BOT_TOKEN),
            ("TELEGRAM_CHAT_ID", cls.TELEGRAM_CHAT_ID),
            ("DATABASE_URL", cls.DATABASE_URL),
        ]

        missing = [name for name, value in required if not value]

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return True


# League configurations
LEAGUE_CONFIG = {
    262: {
        "name": "Liga MX",
        "country": "Mexico",
        "priority": 5,
        "emoji": "🇲🇽"
    },
    39: {
        "name": "Premier League",
        "country": "England",
        "priority": 4,
        "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    },
    140: {
        "name": "La Liga",
        "country": "Spain",
        "priority": 4,
        "emoji": "🇪🇸"
    },
    78: {
        "name": "Bundesliga",
        "country": "Germany",
        "priority": 3,
        "emoji": "🇩🇪"
    },
    135: {
        "name": "Serie A",
        "country": "Italy",
        "priority": 3,
        "emoji": "🇮🇹"
    },
    61: {
        "name": "Ligue 1",
        "country": "France",
        "priority": 3,
        "emoji": "🇫🇷"
    }
}
