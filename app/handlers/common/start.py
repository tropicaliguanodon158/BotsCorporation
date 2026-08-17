from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.database.repositories.users import UserRepository


router = Router(
    name="common_start",
)


@router.message(CommandStart())
async def start_handler(
    message: Message,
    session,
) -> None:
    """
    Обработчик /start.

    Регистрирует пользователя в БД
    и приветствует его.
    """

    if message.from_user is None:
        return

    repository = UserRepository(
        session,
    )

    user, created = await repository.get_or_create(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        username=message.from_user.username,
    )

    if created:
        text = (
            f"Привет, <b>{user.first_name}</b>!\n\n"
            "Ты зарегистрирован в RPG-боте."
        )
    else:
        text = (
            f"С возвращением, "
            f"<b>{user.first_name}</b>!"
        )

    await message.answer(
        text,
    )