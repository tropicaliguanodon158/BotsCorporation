from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.repositories.economy import EconomyRepository
from app.database.repositories.games import GamesRepository
from app.services.games import GamesService


router = Router(name="games_dice")


@router.message(Command("dice"))
async def dice_handler(
    message: Message,
    session,
) -> None:
    if message.from_user is None:
        return

    args = (message.text or "").split()[1:]

    if not args:
        await message.answer(
            "🎲 Использование:\n"
            "<code>/dice 100</code>\n"
            "<code>/dice 100 6</code>\n"
            "<code>/dice 100 6 4</code>"
        )
        return

    try:
        bet = Decimal(args[0])
        sides = int(args[1]) if len(args) >= 2 else 6
        target = int(args[2]) if len(args) >= 3 else None
    except (InvalidOperation, ValueError):
        await message.answer(
            "❌ Неверные параметры ставки."
        )
        return

    repository = GamesRepository(session)
    economy = EconomyRepository(session)

    service = GamesService(
        repository=repository,
        economy_repository=economy,
    )

    try:
        result = await service.dice(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            bet=bet,
            sides=sides,
            target=target,
        )
    except ValueError as exc:
        await message.answer(f"❌ {exc}")
        return

    status = "🎉 Победа!" if result["won"] else "💀 Проигрыш."

    await message.answer(
        f"🎲 <b>Кости</b>\n\n"
        f"Выпало: <b>{result['roll']}</b> из {result['sides']}\n"
        f"Ставка: <b>{result['bet']:.2f}</b>\n\n"
        f"{status}\n"
        f"Выплата: <b>{result['payout']:.2f}</b>"
    )