from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config.settings import get_settings


router = Router(name="founder_panel")


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
        "Доступ к панели основателя подтверждён.\n\n"
        "Разделы панели:\n"
        "⚙️ <code>/founder_settings</code> — настройки\n"
        "💰 <code>/founder_economy</code> — экономика\n"
        "👥 <code>/founder_users</code> — пользователи\n"
        "💬 <code>/founder_chats</code> — чаты\n"
        "🛡 <code>/founder_moderation</code> — модерация\n"
        "🧙 <code>/founder_races</code> — расы\n"
        "🏷 <code>/founder_ranks</code> — ранги\n"
        "✨ <code>/founder_abilities</code> — способности\n"
        "📦 <code>/founder_cases</code> — кейсы\n"
        "🛒 <code>/founder_shop</code> — магазин"
    )