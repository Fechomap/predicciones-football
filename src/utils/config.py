"""Configuration management with Pydantic validation"""
from pydantic import Field, field_validator, model_validator, ConfigDict
from pydantic_settings import BaseSettings
from typing import List, Self


class Config(BaseSettings):
    """Application configuration with automatic validation"""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API-Football
    RAPIDAPI_KEY: str = Field(..., description="API-Football API key")
    RAPIDAPI_HOST: str = Field(
        default="api-football-v1.p.rapidapi.com",
        description="API-Football host"
    )

    # FootyStats API
    FOOTYSTATS_API_KEY: str = Field(..., description="FootyStats API key")
    FOOTYSTATS_BASE_URL: str = Field(
        default="https://api.footystats.org",
        description="FootyStats API base URL"
    )

    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(..., description="Telegram bot token")
    TELEGRAM_CHAT_ID: str = Field(..., description="Telegram chat ID")

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment: development or production")

    # Database URLs
    DATABASE_URL_LOCAL: str = Field(default="postgresql://localhost:5432/football_betting", description="Local database URL")
    DATABASE_URL_PRODUCTION: str = Field(default="", description="Production database URL (Railway)")
    DATABASE_URL: str = Field(default="", description="Active database URL (auto-configured)")

    # Bot Configuration
    ALERT_TIME_MINUTES: int = Field(default=60, ge=1, le=1440, description="Alert time before match")
    MINIMUM_EDGE: float = Field(default=0.05, ge=0.0, le=1.0, description="Minimum edge for value bet")
    CHECK_INTERVAL: int = Field(default=30, ge=1, le=3600, description="Check interval in seconds")
    MIN_CONFIDENCE: int = Field(default=3, ge=1, le=5, description="Minimum confidence rating")
    MAX_ALERTS_PER_DAY: int = Field(default=10, ge=1, le=100, description="Maximum alerts per day")

    # Bankroll Management
    BANKROLL: float = Field(default=1000.0, gt=0, description="Total bankroll amount")
    KELLY_FRACTION: float = Field(default=0.25, gt=0, le=1.0, description="Kelly fraction for safety")
    MAX_STAKE_PERCENTAGE: float = Field(default=0.05, gt=0, le=1.0, description="Max stake as % of bankroll")

    # Form Analysis
    MOMENTUM_MIN_MATCHES: int = Field(default=6, ge=3, le=20, description="Min matches for momentum")
    FORM_MIN_SAMPLE_SIZE: int = Field(default=5, ge=1, le=20, description="Min sample for confidence")

    # Leagues
    ENABLED_LEAGUES: str = Field(default="262", description="Comma-separated league IDs")

    # Server
    PORT: int = Field(default=8000, ge=1, le=65535, description="Server port")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    @model_validator(mode='after')
    def configure_database_url(self) -> Self:
        """Auto-configure DATABASE_URL based on ENVIRONMENT"""
        # If DATABASE_URL is already set (e.g., by Railway), use it
        if self.DATABASE_URL:
            print(f"🔧 Using pre-configured DATABASE_URL")
            return self

        # Otherwise, auto-configure based on ENVIRONMENT
        if self.ENVIRONMENT.lower() == "production":
            if self.DATABASE_URL_PRODUCTION:
                self.DATABASE_URL = self.DATABASE_URL_PRODUCTION
                print(f"🚀 Using PRODUCTION database (Railway)")
            else:
                raise ValueError("DATABASE_URL_PRODUCTION not configured for production environment")
        else:
            self.DATABASE_URL = self.DATABASE_URL_LOCAL
            print(f"💻 Using LOCAL database (development)")

        return self

    @field_validator("ENABLED_LEAGUES")
    @classmethod
    def parse_enabled_leagues(cls, v: str) -> List[int]:
        """Parse comma-separated league IDs into list of integers"""
        try:
            return [int(league_id.strip()) for league_id in v.split(",")]
        except ValueError as e:
            raise ValueError(f"Invalid league IDs format: {v}. Must be comma-separated integers.") from e

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("MINIMUM_EDGE")
    @classmethod
    def validate_minimum_edge(cls, v: float) -> float:
        """Validate minimum edge is reasonable"""
        if v < 0.01:
            raise ValueError("MINIMUM_EDGE too low (< 1%). Recommended: 0.05 (5%)")
        if v > 0.5:
            raise ValueError("MINIMUM_EDGE too high (> 50%). Recommended: 0.05-0.15")
        return v

    @field_validator("KELLY_FRACTION")
    @classmethod
    def validate_kelly_fraction(cls, v: float) -> float:
        """Validate Kelly fraction is safe"""
        if v > 0.5:
            raise ValueError("KELLY_FRACTION > 0.5 is risky. Recommended: 0.25 (quarter Kelly)")
        return v


# Create singleton instance with validation
try:
    config = Config()
except Exception as e:
    print(f"❌ Configuration validation error: {e}")
    print("Please check your .env file and ensure all required variables are set correctly.")
    raise

# Backward compatibility: expose config as class-like object
Config = config  # type: ignore


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
