from __future__ import annotations

import random

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message


router = Router(name="interactions")


@router.message(Command("coin"))
async def coin_handler(
    message: Message,
) -> None:
    result = random.choice(
        (
            "🪙 Орёл!",
            "🪙 Решка!",
        )
    )

    await message.answer(result)


@router.message(Command("8ball"))
async def eight_ball_handler(
    message: Message,
) -> None:
    answers = (
        "🎱 Без сомнений.",
        "🎱 Скорее всего.",
        "🎱 Возможно.",
        "🎱 Спроси позже.",
        "🎱 Сейчас я бы не рассчитывал.",
        "🎱 Определённо нет.",
        "🎱 Определённо да.",
    )

    await message.answer(
        random.choice(answers)
    )


@router.message(Command("choose"))
async def choose_handler(
    message: Message,
) -> None:
    text = (message.text or "").strip()

    parts = text.split(maxsplit=1)

    if len(parts) != 2:
        await message.answer(
            "Использование:\n"
            "<code>/choose вариант1 | вариант2</code>"
        )
        return

    variants = [
        item.strip()
        for item in parts[1].split("|")
        if item.strip()
    ]

    if len(variants) < 2:
        await message.answer(
            "❌ Нужно указать минимум два варианта "
            "через символ <code>|</code>."
        )
        return

    await message.answer(
        "🎯 Я выбираю:\n\n"
        f"<b>{random.choice(variants)}</b>"
    )


@router.message(Command("roll"))
async def roll_handler(
    message: Message,
) -> None:
    text = (message.text or "").strip()
    parts = text.split(maxsplit=1)

    sides = 6

    if len(parts) == 2:
        value = parts[1].strip()

        if not value.isdigit():
            await message.answer(
                "❌ Количество граней должно быть числом."
            )
            return

        sides = int(value)

    if sides < 2 or sides > 1000:
        await message.answer(
            "❌ Количество граней должно быть от 2 до 1000."
        )
        return

    result = random.randint(1, sides)

    await message.answer(
        f"🎲 Бросок D{sides}: <b>{result}</b>"
    )