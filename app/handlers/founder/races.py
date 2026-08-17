from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.filters.founder import FounderFilter
from app.keyboards.founder import (
    founder_races_keyboard,
)

router = Router(name="founder_races")
router.callback_query.filter(FounderFilter())


@router.callback_query(F.data == "founder:races")
async def founder_races(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🧬 <b>Расы</b>\n\n"
        "Управление расами RPG-персонажей.",
        reply_markup=founder_races_keyboard(),
    )


@router.callback_query(F.data == "founder:races:list:1")
async def founder_races_list(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "📋 <b>Список рас</b>\n\n"
        "Список будет загружаться из CharacterRepository.",
        reply_markup=founder_races_keyboard(),
    )


@router.callback_query(F.data == "founder:races:create")
async def founder_races_create(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "➕ <b>Создание расы</b>\n\n"
        "FSM-форма создания будет подключена следующим этапом.",
        reply_markup=founder_races_keyboard(),
    )


@router.callback_query(F.data == "founder:races:edit")
async def founder_races_edit(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "✏️ <b>Редактирование рас</b>\n\n"
        "Выберите расу для изменения.",
        reply_markup=founder_races_keyboard(),
    )


@router.callback_query(F.data == "founder:races:stats")
async def founder_races_stats(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "📊 <b>Характеристики рас</b>\n\n"
        "Управление базовыми характеристиками рас.",
        reply_markup=founder_races_keyboard(),
    )


@router.callback_query(F.data == "founder:races:delete")
async def founder_races_delete(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🗑 <b>Удаление / отключение</b>\n\n"
        "Удаление будет выполняться только после "
        "подтверждения Founder.",
        reply_markup=founder_races_keyboard(),
    )