"""
Application configuration.

Все настройки приложения берутся из переменных окружения
и/или файла .env.

Никаких токенов, паролей и других секретов непосредственно
в исходном коде быть не должно.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============================================================================
# SETTINGS
# ============================================================================


class Settings(BaseSettings):
    """
    Глобальные настройки приложения.
    """

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    APP_NAME: str = "Telegram RPG Bot"

    ENVIRONMENT: str = Field(
        default="development",
        description="development / testing / production",
    )

    DEBUG: bool = False

    # ------------------------------------------------------------------
    # Telegram
    # ------------------------------------------------------------------

    BOT_TOKEN: str = Field(
        ...,
        description="Telegram Bot API token",
    )

    # Telegram ID основателя.

    FOUNDER_ID: int = Field(
        ...,
        description="Telegram user ID of the bot founder",
    )

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    DATABASE_URL: str = Field(
        ...,
        description="SQLAlchemy async database URL",
    )

    DATABASE_ECHO: bool = False

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    LOG_LEVEL: str = "INFO"

    LOG_FILE: str = "logs/bot.log"

    # ------------------------------------------------------------------
    # Timezone
    # ------------------------------------------------------------------

    DEFAULT_TIMEZONE: str = "Europe/Warsaw"

    # ------------------------------------------------------------------
    # Economy defaults
    # ------------------------------------------------------------------

    DEFAULT_MESSAGE_REWARD: float = 1.0

    DEFAULT_PHOTO_REWARD: float = 3.0

    DEFAULT_VIDEO_REWARD: float = 5.0

    DEFAULT_MESSAGE_COOLDOWN: int = 10

    # ------------------------------------------------------------------
    # Anti-flood
    # ------------------------------------------------------------------

    ANTIFLOOD_ENABLED: bool = True

    ANTIFLOOD_MESSAGES: int = 5

    ANTIFLOOD_INTERVAL: int = 10

    ANTIFLOOD_MUTE_SECONDS: int = 60

    # ------------------------------------------------------------------
    # Rewards
    # ------------------------------------------------------------------

    HOURLY_REWARD_ENABLED: bool = True

    HOURLY_REWARD_AMOUNT: float = 100.0

    # ------------------------------------------------------------------
    # Activity
    # ------------------------------------------------------------------

    PASSIVE_INCOME_REQUIRED_MESSAGES: int = 30

    # ------------------------------------------------------------------
    # Founder
    # ------------------------------------------------------------------

    FOUNDER_PANEL_ENABLED: bool = True

    # ------------------------------------------------------------------
    # Telegram API behaviour
    # ------------------------------------------------------------------

    DROP_PENDING_UPDATES: bool = True

    # ------------------------------------------------------------------
    # Configuration loading
    # ------------------------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        """
        Проверяет окружение.
        """

        allowed = {
            "development",
            "testing",
            "production",
        }

        value = value.lower().strip()

        if value not in allowed:
            raise ValueError(
                "ENVIRONMENT must be one of: "
                "development, testing, production"
            )

        return value

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """
        Проверяет уровень логирования.
        """

        allowed = {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }

        value = value.upper().strip()

        if value not in allowed:
            raise ValueError(
                "LOG_LEVEL must be one of: "
                "DEBUG, INFO, WARNING, ERROR, CRITICAL"
            )

        return value

    @field_validator("BOT_TOKEN")
    @classmethod
    def validate_bot_token(cls, value: str) -> str:
        """
        Минимальная проверка Telegram Bot Token.
        """

        value = value.strip()

        if not value:
            raise ValueError("BOT_TOKEN cannot be empty")

        if ":" not in value:
            raise ValueError(
                "BOT_TOKEN does not look like a valid Telegram bot token"
            )

        return value

    @field_validator("FOUNDER_ID")
    @classmethod
    def validate_founder_id(cls, value: int) -> int:
        """
        Telegram ID должен быть положительным.
        """

        if value <= 0:
            raise ValueError(
                "FOUNDER_ID must be a positive Telegram user ID"
            )

        return value


# ============================================================================
# SETTINGS INSTANCE
# ============================================================================


@lru_cache
def get_settings() -> Settings:
    """
    Возвращает единственный экземпляр Settings.

    Используем cache, чтобы .env не читался заново
    при каждом обращении к настройкам.
    """

    return Settings()


settings = get_settings()


__all__ = [
    "Settings",
    "settings",
    "get_settings",
]