from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.repositories.economy import EconomyRepository
from app.services.economy import EconomyService


router = Router(
    name="economy_balance",
)


@router.message(Command("balance"))
async def balance_handler(
    message: Message,
    session,
) -> None:
    """
    Показывает баланс пользователя.
    """

    if message.from_user is None:
        return

    repository = EconomyRepository(
        session,
    )

    service = EconomyService(
        repository,
    )

    balance = await service.get_balance(
        message.from_user.id,
    )

    gems = await service.get_gems(
        message.from_user.id,
    )

    await message.answer(
        "<b>💰 Кошелёк</b>\n\n"
        f"💵 Баланс: <b>{balance:.2f}</b>\n"
        f"💎 Гемы: <b>{gems}</b>"
    )