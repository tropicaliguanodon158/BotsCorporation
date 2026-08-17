from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.repositories.users import UserRepository


router = Router(
    name="common_profile",
)


@router.message(Command("profile"))
async def profile_handler(
    message: Message,
    session,
) -> None:
    """
    Показывает базовый профиль пользователя.
    """

    if message.from_user is None:
        return

    repository = UserRepository(
        session,
    )

    user = await repository.get_by_id(
        message.from_user.id,
    )

    if user is None:
        await message.answer(
            "❌ Пользователь не найден."
        )
        return

    username = (
        f"@{user.username}"
        if user.username
        else "не указан"
    )

    await message.answer(
        "<b>👤 Профиль</b>\n\n"
        f"Имя: <b>{user.first_name}</b>\n"
        f"Username: {username}\n"
        f"Уровень: <b>{user.level}</b>\n"
        f"XP: <b>{user.xp}</b>\n"
        f"Репутация: <b>{user.reputation}</b>\n\n"
        f"Сообщений: <b>{user.message_count}</b>\n"
        f"За сегодня: <b>{user.daily_message_count}</b>"
    )