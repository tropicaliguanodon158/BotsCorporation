from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.filters.founder import FounderFilter
from app.keyboards.founder import founder_back_keyboard

router = Router(name="founder_moderation")
router.callback_query.filter(FounderFilter())


@router.callback_query(F.data == "founder:moderation")
async def founder_moderation(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🛡 <b>Модерация</b>\n\n"
        "Управление глобальными параметрами модерации.",
        reply_markup=founder_back_keyboard("founder:main"),
    )


@router.callback_query(F.data == "founder:user:moderation")
async def founder_user_moderation(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🛡 <b>Модерация пользователя</b>\n\n"
        "Действия с модерацией конкретного пользователя "
        "будут подключены через ModerationService.",
        reply_markup=founder_back_keyboard("founder:users"),
    )