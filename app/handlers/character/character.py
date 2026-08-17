from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.database.repositories.characters import CharacterRepository
from app.services.character import CharacterService


router = Router(name="character")


@router.message(Command("character"))
async def character_handler(
    message: Message,
    session,
) -> None:
    if message.from_user is None:
        return

    repository = CharacterRepository(session)
    service = CharacterService(repository)

    character = await service.get_character(
        message.from_user.id,
    )

    if character is None:
        await message.answer(
            "🧙 У тебя ещё нет персонажа.\n"
            "Создай его командой:\n"
            "<code>/character_create Имя</code>"
        )
        return

    await message.answer(
        "🧙 <b>Персонаж</b>\n\n"
        f"👤 <b>{character.name}</b>\n"
        f"⭐ Уровень: {character.level}\n"
        f"✨ XP: {character.xp}\n"
        f"❤️ HP: {character.hp}/{character.max_hp}\n"
        f"⚔️ Сила: {character.strength}\n"
        f"🛡 Защита: {character.defense}\n"
        f"🍀 Удача: {character.luck}\n"
        f"⚡ Скорость: {character.speed}\n"
        f"🧠 Интеллект: {character.intelligence}\n"
        f"🏷 Титул: {character.title or '—'}"
    )


@router.message(Command("character_create"))
async def character_create_handler(
    message: Message,
    command: CommandObject,
    session,
) -> None:
    if message.from_user is None:
        return

    name = (command.args or "").strip()

    if not name:
        await message.answer(
            "Использование:\n"
            "<code>/character_create Имя</code>"
        )
        return

    repository = CharacterRepository(session)
    service = CharacterService(repository)

    try:
        character = await service.create_character(
            user_id=message.from_user.id,
            name=name,
        )
    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )
        return

    await message.answer(
        "🎉 <b>Персонаж создан!</b>\n\n"
        f"👤 Имя: <b>{character.name}</b>\n"
        f"⭐ Уровень: {character.level}\n"
        f"❤️ HP: {character.hp}/{character.max_hp}\n"
        f"⚔️ Сила: {character.strength}\n"
        f"🛡 Защита: {character.defense}"
    )


@router.message(Command("rename"))
async def rename_handler(
    message: Message,
    command: CommandObject,
    session,
) -> None:
    if message.from_user is None:
        return

    name = (command.args or "").strip()

    if not name:
        await message.answer(
            "Использование:\n"
            "<code>/rename НовоеИмя</code>"
        )
        return

    repository = CharacterRepository(session)
    service = CharacterService(repository)

    try:
        character = await service.rename(
            user_id=message.from_user.id,
            name=name,
        )
    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )
        return

    await message.answer(
        f"✅ Имя персонажа изменено на "
        f"<b>{character.name}</b>."
    )


@router.message(Command("races"))
async def races_handler(
    message: Message,
    session,
) -> None:
    repository = CharacterRepository(session)
    service = CharacterService(repository)

    races = await service.get_active_races()

    if not races:
        await message.answer(
            "🧬 Сейчас доступных рас нет."
        )
        return

    lines = ["🧬 <b>Доступные расы</b>\n"]

    for race in races:
        lines.append(
            f"• <b>{race.name}</b>\n"
            f"  {race.description or 'Без описания'}\n"
            f"  ❤️ {race.base_hp} | "
            f"⚔️ {race.base_strength} | "
            f"🛡 {race.base_defense}"
        )

    await message.answer(
        "\n\n".join(lines)
    )


@router.message(Command("race"))
async def race_handler(
    message: Message,
    command: CommandObject,
    session,
) -> None:
    if message.from_user is None:
        return

    args = (command.args or "").split()

    if len(args) != 1 or not args[0].isdigit():
        await message.answer(
            "Использование:\n"
            "<code>/race ID_расы</code>\n\n"
            "Список рас: <code>/races</code>"
        )
        return

    race_id = int(args[0])

    repository = CharacterRepository(session)
    service = CharacterService(repository)

    try:
        character = await service.change_race(
            user_id=message.from_user.id,
            race_id=race_id,
        )
    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )
        return

    await message.answer(
        f"🧬 Раса персонажа <b>{character.name}</b> изменена.\n\n"
        f"❤️ HP: {character.hp}/{character.max_hp}\n"
        f"⚔️ Сила: {character.strength}\n"
        f"🛡 Защита: {character.defense}\n"
        f"🍀 Удача: {character.luck}\n"
        f"⚡ Скорость: {character.speed}\n"
        f"🧠 Интеллект: {character.intelligence}"
    )