from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config.settings import get_settings


router = Router(name="founder_chats")


def _is_founder(user_id: int) -> bool:
    settings = get_settings()

    return (
        settings.FOUNDER_PANEL_ENABLED
        and user_id == settings.FOUNDER_ID
    )


@router.message(Command("founder_chats"))
async def founder_chats_handler(
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
        "💬 <b>Управление чатами</b>\n\n"
        "Раздел подготовлен для управления настройками "
        "конкретных Telegram-чатов.\n\n"
        "Планируемые операции:\n"
        "• просмотр подключённых чатов;\n"
        "• просмотр настроек чата;\n"
        "• изменение настроек;\n"
        "• включение/отключение функций;\n"
        "• сброс динамических настроек.\n\n"
        "Используй Founder Panel для перехода к нужному разделу."
    )