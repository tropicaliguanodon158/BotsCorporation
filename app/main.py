from __future__ import annotations

import asyncio
import logging

from aiogram.exceptions import TelegramNetworkError

from app.bot.bot import create_bot
from app.bot.dispatcher import create_dispatcher
from app.config.settings import settings
from app.database.database import (
    close_database,
    init_database,
)


# ============================================================================
# LOGGING
# ============================================================================


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(
            logging,
            settings.LOG_LEVEL,
            logging.INFO,
        ),
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )


# ============================================================================
# POLLING SUPERVISOR
# ============================================================================


async def run_polling(
    dispatcher,
    bot,
) -> None:
    """
    Запускает Telegram polling с автоматическим восстановлением
    после временных сетевых ошибок.

    Это особенно важно для постоянной работы через VPN.

    Стратегия:

        ошибка #1  -> 2 секунды
        ошибка #2  -> 4 секунды
        ошибка #3  -> 8 секунд
        ...
        максимум  -> 60 секунд

    После успешного запуска polling backoff сбрасывается.

    Важно:

    Мы не перезапускаем polling после обычного завершения.
    Завершение без исключения считается штатной остановкой.
    """

    logger = logging.getLogger(
        "app.polling"
    )

    retry_delay = 2
    max_retry_delay = 60

    while True:
        try:
            logger.info(
                "Starting Telegram polling..."
            )

            await dispatcher.start_polling(
                bot,
            )

            logger.info(
                "Telegram polling stopped normally."
            )

            return

        except TelegramNetworkError as exc:
            logger.warning(
                "Telegram network error: %s. "
                "Retrying in %s seconds.",
                exc,
                retry_delay,
            )

            await asyncio.sleep(
                retry_delay
            )

            retry_delay = min(
                retry_delay * 2,
                max_retry_delay,
            )

        except (
            asyncio.TimeoutError,
            ConnectionError,
            OSError,
        ) as exc:
            logger.warning(
                "Temporary connection error: %s. "
                "Retrying in %s seconds.",
                exc,
                retry_delay,
            )

            await asyncio.sleep(
                retry_delay
            )

            retry_delay = min(
                retry_delay * 2,
                max_retry_delay,
            )


# ============================================================================
# APPLICATION
# ============================================================================


async def main() -> None:
    configure_logging()

    logger = logging.getLogger(
        __name__
    )

    bot = create_bot()
    dispatcher = create_dispatcher()

    try:
        logger.info(
            "Starting %s",
            settings.APP_NAME,
        )

        # ====================================================================
        # DATABASE
        # ====================================================================

        await init_database()

        logger.info(
            "Database initialized."
        )

        # ====================================================================
        # TELEGRAM WEBHOOK
        # ====================================================================

        await bot.delete_webhook(
            drop_pending_updates=(
                settings.DROP_PENDING_UPDATES
            ),
        )

        # ====================================================================
        # POLLING
        # ====================================================================

        await run_polling(
            dispatcher,
            bot,
        )

    finally:
        logger.info(
            "Shutting down..."
        )

        try:
            await bot.session.close()
        except Exception:
            logger.exception(
                "Failed to close Telegram session."
            )

        try:
            await close_database()
        except Exception:
            logger.exception(
                "Failed to close database."
            )

        logger.info(
            "Application stopped."
        )


# ============================================================================
# ENTRY POINT
# ============================================================================


if __name__ == "__main__":
    try:
        asyncio.run(
            main()
        )

    except KeyboardInterrupt:
        pass
