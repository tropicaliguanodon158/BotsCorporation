from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.repositories.economy import EconomyRepository
from app.services.bank import BankService


router = Router(
    name="economy_bank",
)


@router.message(Command("pay"))
@router.message(Command("transfer"))
async def transfer_handler(
    message: Message,
    session,
) -> None:
    """
    Перевод денег другому пользователю.

    Использование:

        ответить на сообщение пользователя:
        /pay 100

    или:

        /transfer 100
    """

    if message.from_user is None:
        return

    if message.reply_to_message is None:
        await message.answer(
            "❌ Используй команду ответом на сообщение пользователя:\n\n"
            "<code>/pay 100</code>"
        )
        return

    target = message.reply_to_message.from_user

    if target is None:
        await message.answer(
            "❌ Не удалось определить получателя."
        )
        return

    parts = (message.text or "").split()

    if len(parts) != 2:
        await message.answer(
            "❌ Использование:\n"
            "<code>/pay 100</code>"
        )
        return

    try:
        amount = Decimal(parts[1].replace(",", "."))
    except (InvalidOperation, ValueError):
        await message.answer(
            "❌ Сумма должна быть числом."
        )
        return

    if amount <= 0:
        await message.answer(
            "❌ Сумма должна быть больше нуля."
        )
        return

    service = BankService(
        economy_repository=EconomyRepository(session),
    )

    try:
        result = await service.transfer(
            sender_id=message.from_user.id,
            receiver_id=target.id,
            amount=amount,
        )
    except ValueError:
        await message.answer(
            "❌ Некорректная сумма."
        )
        return

    if not result.success:
        if result.reason == "insufficient_balance":
            text = "❌ Недостаточно средств."

        elif result.reason == "same_user":
            text = "❌ Нельзя переводить деньги самому себе."

        else:
            text = "❌ Перевод не выполнен."

        await message.answer(text)
        return

    await message.answer(
        "💸 <b>Перевод выполнен</b>\n\n"
        f"Получатель: {target.full_name}\n"
        f"Сумма: <b>{result.amount:.2f}</b>"
    )