from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config.settings import get_settings
from app.keyboards.founder import founder_main_keyboard


router = Router(
    name="founder_panel",
)


def _is_founder(user_id: int) -> bool:
    settings = get_settings()

    return (
        settings.FOUNDER_PANEL_ENABLED
        and user_id == settings.FOUNDER_ID
    )


@router.message(Command("founder"))
async def founder_panel_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    if not _is_founder(message.from_user.id):
        await message.answer(
            "❌ Доступ запрещён."
        )
        return

    await message.answer(
        "👑 <b>Founder Panel</b>\n\n"
        "Добро пожаловать в панель основателя.\n"
        "Выбери нужный раздел:",
        reply_markup=founder_main_keyboard(),
    )