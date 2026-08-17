from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.repositories.economy import EconomyRepository
from app.database.repositories.games import GamesRepository
from app.services.games import GamesService


router = Router(name="games_roulette")


@router.message(Command("roulette"))
async def roulette_handler(
    message: Message,
    session,
) -> None:
    if message.from_user is None:
        return

    args = (message.text or "").split()[1:]

    if len(args) < 2:
        await message.answer(
            "🎰 Использование:\n"
            "<code>/roulette 100 red</code>\n"
            "<code>/roulette 100 black</code>\n"
            "<code>/roulette 100 green</code>"
        )
        return

    try:
        bet = Decimal(args[0])
    except InvalidOperation:
        await message.answer(
            "❌ Неверная сумма ставки."
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
        result = await service.roulette(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            bet=bet,
            selection=selection,
        )
    except ValueError as exc:
        await message.answer(f"❌ {exc}")
        return

    status = "🎉 Победа!" if result["won"] else "💀 Проигрыш."

    await message.answer(
        f"🎰 <b>Рулетка</b>\n\n"
        f"Выпало: <b>{result['number']}</b>\n"
        f"Цвет: <b>{result['color']}</b>\n"
        f"Ставка: <b>{result['bet']:.2f}</b>\n\n"
        f"{status}\n"
        f"Выплата: <b>{result['payout']:.2f}</b>"
    )