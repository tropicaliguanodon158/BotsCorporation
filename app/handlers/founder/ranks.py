from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.filters.founder import FounderFilter
from app.keyboards.founder import founder_ranks_keyboard

router = Router(name="founder_ranks")
router.callback_query.filter(FounderFilter())


@router.callback_query(F.data == "founder:ranks")
async def founder_ranks(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🏅 <b>Ранги</b>\n\n"
        "Управление рангами персонажей.",
        reply_markup=founder_ranks_keyboard(),
    )


@router.callback_query(F.data == "founder:ranks:list:1")
async def founder_ranks_list(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "📋 <b>Список рангов</b>\n\n"
        "Список будет загружаться из CharacterRepository.",
        reply_markup=founder_ranks_keyboard(),
    )


@router.callback_query(F.data == "founder:ranks:create")
async def founder_ranks_create(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "➕ <b>Создание ранга</b>\n\n"
        "FSM-форма создания будет подключена следующим этапом.",
        reply_markup=founder_ranks_keyboard(),
    )


@router.callback_query(F.data == "founder:ranks:edit")
async def founder_ranks_edit(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "✏️ <b>Редактирование рангов</b>\n\n"
        "Выберите ранг для изменения.",
        reply_markup=founder_ranks_keyboard(),
    )


@router.callback_query(F.data == "founder:ranks:order")
async def founder_ranks_order(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "📊 <b>Порядок рангов</b>\n\n"
        "Настройка порядка и приоритетов рангов.",
        reply_markup=founder_ranks_keyboard(),
    )


@router.callback_query(F.data == "founder:ranks:delete")
async def founder_ranks_delete(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🗑 <b>Удаление / отключение ранга</b>\n\n"
        "Удаление будет выполняться только после "
        "подтверждения Founder.",
        reply_markup=founder_ranks_keyboard(),
    )