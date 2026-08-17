from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.repositories.economy import EconomyRepository
from app.database.repositories.games import GamesRepository
from app.services.games import GamesService


router = Router(name="games_coinflip")


@router.message(Command("coinflip"))
async def coinflip_handler(
    message: Message,
    session,
) -> None:
    """
    /coinflip <ставка> <heads|tails>

    Примеры:

        /coinflip 100 heads
        /coinflip 100 tails

    Также принимаются:

        орёл
        орел
        решка
    """

    if message.from_user is None:
        return

    args = (
        message.text or ""
    ).split()[1:]

    if len(args) < 2:
        await message.answer(
            "🪙 <b>Монетка</b>\n\n"
            "Использование:\n"
            "<code>/coinflip 100 heads</code>\n"
            "<code>/coinflip 100 tails</code>\n\n"
            "Можно также написать "
            "<code>орёл</code> или "
            "<code>решка</code>."
        )
        return

    try:
        bet = Decimal(args[0])
    except InvalidOperation:
        await message.answer(
            "❌ Неверный размер ставки."
        )
        return

    selection = args[1]

    repository = GamesRepository(session)
    economy = EconomyRepository(session)

    service = GamesService(
        repository=repository,
        economy_repository=economy,
    )

    try:
        result = await service.coinflip(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            bet=bet,
            selection=selection,
        )

    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )
        return

    result_names = {
        "heads": "орёл",
        "tails": "решка",
    }

    selected_name = result_names.get(
        result["selection"],
        result["selection"],
    )

    result_name = result_names.get(
        result["result"],
        result["result"],
    )

    if result["won"]:
        status = "🎉 <b>Победа!</b>"
    else:
        status = "💀 <b>Проигрыш.</b>"

    await message.answer(
        "🪙 <b>Монетка</b>\n\n"
        f"Вы выбрали: <b>{selected_name}</b>\n"
        f"Выпало: <b>{result_name}</b>\n"
        f"Ставка: <b>{result['bet']:.2f}</b>\n\n"
        f"{status}\n"
        f"Выплата: <b>{result['payout']:.2f}</b>"
    )


__all__ = [
    "router",
]