from __future__ import annotations

import asyncio

from app.bot.bot import create_bot
from app.bot.dispatcher import create_dispatcher
from app.config.settings import settings
from app.database.database import close_database, init_database


async def main() -> None:
    """
    Главная точка запуска Telegram-бота.

    Порядок запуска:

        1. Инициализация БД.
        2. Создание Bot.
        3. Создание Dispatcher.
        4. Запуск polling.
        5. Корректное завершение при остановке.
    """

    print(
        f"Starting {settings.APP_NAME} "
        f"in {settings.ENVIRONMENT} environment..."
    )

    await init_database()

    bot = create_bot()
    dispatcher = create_dispatcher()

    try:
        print("Bot is running.")

        await bot.delete_webhook(
            drop_pending_updates=settings.DROP_PENDING_UPDATES,
        )

        await dispatcher.start_polling(
            bot,
        )

    finally:
        await bot.session.close()
        await close_database()

        print("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())