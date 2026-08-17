from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


# ============================================================================
# PATHS
# ============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

LOG_FILE = LOG_DIR / "bot.log"


# ============================================================================
# SETTINGS
# ============================================================================

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
).upper()

MAX_LOG_SIZE = 10 * 1024 * 1024
BACKUP_COUNT = 5


# ============================================================================
# FORMAT
# ============================================================================

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)-8s | "
    "%(name)s | "
    "%(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ============================================================================
# LEVEL
# ============================================================================

def _get_log_level() -> int:
    """
    Преобразует строковое значение уровня логирования
    в значение logging.

    Если в .env указано неизвестное значение,
    используется INFO.
    """

    return getattr(
        logging,
        LOG_LEVEL,
        logging.INFO,
    )


# ============================================================================
# LOGGER SETUP
# ============================================================================

def setup_logging() -> logging.Logger:
    """
    Настраивает основной логгер приложения.

    Логи одновременно пишутся:

        1. В консоль.
        2. В logs/bot.log.

    Файл автоматически ротируется при достижении
    максимального размера.
    """

    logger = logging.getLogger("telegram_rpg_bot")

    # Не создаём handlers повторно при повторном вызове.
    if logger.handlers:
        return logger

    logger.setLevel(_get_log_level())

    logger.propagate = False

    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )

    # ------------------------------------------------------------------
    # Console handler
    # ------------------------------------------------------------------

    console_handler = logging.StreamHandler()

    console_handler.setLevel(
        _get_log_level()
    )

    console_handler.setFormatter(
        formatter
    )

    # ------------------------------------------------------------------
    # File handler
    # ------------------------------------------------------------------

    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )

    file_handler.setLevel(
        _get_log_level()
    )

    file_handler.setFormatter(
        formatter
    )

    # ------------------------------------------------------------------
    # Register handlers
    # ------------------------------------------------------------------

    logger.addHandler(
        console_handler
    )

    logger.addHandler(
        file_handler
    )

    logger.info(
        "Логирование приложения инициализировано."
    )

    return logger


# ============================================================================
# DEFAULT LOGGER
# ============================================================================

logger = setup_logging()


# ============================================================================
# PUBLIC HELPERS
# ============================================================================

def get_logger(
    name: str | None = None,
) -> logging.Logger:
    """
    Возвращает логгер приложения.

    Пример:

        from app.utils.logger import get_logger

        logger = get_logger(__name__)

        logger.info("Бот запущен.")
    """

    if not name:
        return logger

    return logging.getLogger(
        f"telegram_rpg_bot.{name}"
    )