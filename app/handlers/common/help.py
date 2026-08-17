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
        "/profile — профиль\n"
        "/balance — баланс и гемы\n\n"

        "<b>Экономика:</b>\n"
        "/hourly — часовая награда\n"
        "/daily — ежедневная награда\n"
        "/pay — перевод денег ответом на сообщение\n\n"

        "<b>Магазин:</b>\n"
        "/shop — список товаров\n"
        "/buy ID [количество] — купить предмет\n"
        "/sell ID [количество] — продать предмет\n\n"

        "<b>Игры:</b>\n"
        "/dice — бросок кубика\n"
        "/roulette — рулетка\n"
        "/duel — дуэль\n\n"

        "💬 Награды за обычную активность "
        "начисляются автоматически."
    )