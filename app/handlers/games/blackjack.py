from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.database.repositories.economy import EconomyRepository
from app.database.repositories.games import GamesRepository
from app.services.games import GamesService


router = Router(name="blackjack")


@router.message(Command("blackjack"))
async def blackjack_handler(
    message: Message,
    command: CommandObject,
    session,
) -> None:
    if message.from_user is None:
        return

    args = (command.args or "").split()

    if not args:
        await message.answer(
            "🃏 <b>Блэкджек</b>\n\n"
            "Использование:\n"
            "<code>/blackjack СТАВКА</code>\n\n"
            "Пример:\n"
            "<code>/blackjack 100</code>"
        )
        return

    if len(args) != 1:
        await message.answer(
            "❌ Укажи только размер ставки."
        )
        return

    try:
        amount = int(args[0])
    except ValueError:
        await message.answer(
            "❌ Ставка должна быть целым числом."
        )
        return

    if amount <= 0:
        await message.answer(
            "❌ Ставка должна быть больше нуля."
        )
        return

    repository = GamesRepository(session)
    economy_repository = EconomyRepository(session)

    service = GamesService(
        repository=repository,
        economy_repository=economy_repository,
    )

    blackjack = getattr(service, "blackjack", None)

    if blackjack is None:
        await message.answer(
            "🃏 Блэкджек пока находится на этапе подключения "
            "к игровому сервису."
        )
        return

    try:
        result = await blackjack(
            user_id=message.from_user.id,
            chat_id=(
                message.chat.id
                if message.chat
                else None
            ),
            bet=amount,
        )
    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )
        return

    await message.answer(
        "🃏 <b>Блэкджек</b>\n\n"
        f"🎲 Результат: <b>{result.get('result', '—')}</b>\n"
        f"💰 Ставка: <b>{result.get('bet', amount)}</b>\n"
        f"💵 Выплата: <b>{result.get('payout', 0)}</b>"
    )