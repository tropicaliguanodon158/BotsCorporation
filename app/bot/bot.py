from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config.settings import settings


def create_bot() -> Bot:
    """
    Создаёт и возвращает экземпляр Telegram-бота.

    Отдельная функция нужна для того, чтобы объект бота
    создавался централизованно и в дальнейшем его было
    удобно использовать в других частях приложения.
    """

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    return bot