from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.database.repositories.characters import CharacterRepository


router = Router(name="character_abilities")


@router.message(Command("abilities"))
async def abilities_handler(
    message: Message,
    session,
) -> None:
    if message.from_user is None:
        return

    repository = CharacterRepository(session)

    abilities = await repository.get_character_abilities(
        message.from_user.id,
    )

    if not abilities:
        await message.answer(
            "✨ У твоего персонажа пока нет способностей."
        )
        return

    lines = [
        "✨ <b>Способности персонажа</b>",
        "",
    ]

    for character_ability in abilities:
        ability = await repository.get_ability(
            character_ability.ability_id,
        )

        if ability is None:
            continue

        lines.append(
            f"🔹 <b>{ability.name}</b>\n"
            f"   {ability.description or 'Без описания'}\n"
            f"   Тип: {ability.ability_type}\n"
            f"   Эффект: {ability.effect_value}\n"
            f"   Перезарядка: {ability.cooldown_seconds} сек."
        )

    if len(lines) == 2:
        await message.answer(
            "✨ У твоего персонажа пока нет доступных способностей."
        )
        return

    await message.answer("\n\n".join(lines))


@router.message(Command("ability"))
async def ability_handler(
    message: Message,
    command: CommandObject,
    session,
) -> None:
    if message.from_user is None:
        return

    argument = (command.args or "").strip()

    if not argument:
        await message.answer(
            "Использование:\n"
            "<code>/ability ID</code>\n\n"
            "Список способностей: <code>/abilities</code>"
        )
        return

    if not argument.isdigit():
        await message.answer(
            "❌ ID способности должен быть числом."
        )
        return

    ability_id = int(argument)

    repository = CharacterRepository(session)

    character_ability = await repository.get_character_ability(
        user_id=message.from_user.id,
        ability_id=ability_id,
    )

    if character_ability is None or not character_ability.is_active:
        await message.answer(
            "❌ У твоего персонажа нет этой способности."
        )
        return

    ability = await repository.get_ability(ability_id)

    if ability is None or not ability.is_active:
        await message.answer(
            "❌ Способность недоступна."
        )
        return

    await message.answer(
        "✨ <b>Способность</b>\n\n"
        f"🔹 <b>{ability.name}</b>\n"
        f"📝 {ability.description or 'Без описания'}\n"
        f"⚔️ Тип: {ability.ability_type}\n"
        f"💥 Эффект: {ability.effect_value}\n"
        f"⏱ Длительность: {ability.duration_seconds} сек.\n"
        f"🔄 Перезарядка: {ability.cooldown_seconds} сек."
    )