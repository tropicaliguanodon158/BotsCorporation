from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.repositories.economy import EconomyRepository
from app.database.repositories.games import GamesRepository
from app.services.games import GamesService


router = Router(name="games_duel")


@router.message(Command("duel"))
async def duel_handler(
    message: Message,
    session,
) -> None:
    if message.from_user is None:
        return

    if message.reply_to_message is None:
        await message.answer(
            "⚔️ Ответь на сообщение пользователя и напиши:\n"
            "<code>/duel 100</code>"
        )
        return

    opponent = message.reply_to_message.from_user

    if opponent is None:
        return

    args = (message.text or "").split()[1:]

    if not args:
        await message.answer(
            "⚔️ Укажи размер ставки:\n"
            "<code>/duel 100</code>"
        )
        return

    try:
        bet = Decimal(args[0])
    except InvalidOperation:
        await message.answer(
            "❌ Неверная сумма ставки."
        )
        return

    repository = GamesRepository(session)
    economy = EconomyRepository(session)

    service = GamesService(
        repository=repository,
        economy_repository=economy,
    )

    try:
        result = await service.duel(
            creator_id=message.from_user.id,
            opponent_id=opponent.id,
            chat_id=message.chat.id,
            bet=bet,
        )
    except ValueError as exc:
        await message.answer(f"❌ {exc}")
        return

    winner_id = result["winner_id"]

    if winner_id == message.from_user.id:
        winner_text = "🏆 Победил ты!"
    elif winner_id == opponent.id:
        winner_text = "🏆 Победил соперник!"
    else:
        winner_text = "🏆 Определён победитель!"

    await message.answer(
        f"⚔️ <b>Дуэль</b>\n\n"
        f"Ставка: <b>{result['bet']:.2f}</b>\n"
        f"{winner_text}\n\n"
        f"💰 Выплата победителю: "
        f"<b>{result['winner_payout']:.2f}</b>"
    )