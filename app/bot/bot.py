from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config.settings import settings


def create_bot() -> Bot:
    """
    Создаёт и возвращает экземпляр Telegram-бота.

    Конфигурация берётся из app.config.settings.
    """

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    return bot