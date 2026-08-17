from __future__ import annotations

import asyncio
import logging

from app.bot.bot import create_bot
from app.bot.dispatcher import create_dispatcher
from app.config.settings import settings
from app.database.database import close_database, init_database


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


async def main() -> None:
    configure_logging()

    logger = logging.getLogger(__name__)

    bot = create_bot()
    dispatcher = create_dispatcher()

    try:
        logger.info(
            "Starting %s",
            settings.APP_NAME,
        )

        await init_database()

        logger.info(
            "Database initialized."
        )

        await bot.delete_webhook(
            drop_pending_updates=settings.DROP_PENDING_UPDATES,
        )

        logger.info(
            "Starting Telegram polling..."
        )

        await dispatcher.start_polling(
            bot,
        )

    finally:
        logger.info(
            "Shutting down..."
        )

        await bot.session.close()
        await close_database()

        logger.info(
            "Application stopped."
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass