from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message


router = Router(
    name="common_help",
)


@router.message(Command("help"))
async def help_handler(
    message: Message,
) -> None:
    """
    Основная справка по доступным командам.
    """

    await message.answer(
        "<b>🤖 Команды бота</b>\n\n"
        "<b>Основные:</b>\n"
        "/start — регистрация\n"
        "/help — эта справка\n"
        "/profile — профиль персонажа\n"
        "/balance — баланс и гемы\n\n"
        "<b>Экономика:</b>\n"
        "/hourly — часовая награда\n"
        "/daily — ежедневная награда\n\n"
        "Награды за обычную активность "
        "начисляются автоматически."
    )