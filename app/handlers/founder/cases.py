from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.filters.founder import FounderFilter
from app.keyboards.founder import (
    founder_cases_keyboard,
)

router = Router(name="founder_cases")
router.callback_query.filter(FounderFilter())


@router.callback_query(F.data == "founder:cases")
async def founder_cases(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🎁 <b>Кейсы</b>\n\n"
        "Управление кейсами и их содержимым.",
        reply_markup=founder_cases_keyboard(),
    )


@router.callback_query(
    F.data == "founder:cases:list:1"
)
async def founder_cases_list(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "📋 <b>Список кейсов</b>\n\n"
        "Список будет загружаться из "
        "сервиса кейсов.",
        reply_markup=founder_cases_keyboard(),
    )


@router.callback_query(
    F.data == "founder:cases:create"
)
async def founder_cases_create(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "➕ <b>Создание кейса</b>\n\n"
        "FSM-форма создания кейса будет "
        "подключена следующим этапом.",
        reply_markup=founder_cases_keyboard(),
    )


@router.callback_query(
    F.data == "founder:cases:edit"
)
async def founder_cases_edit(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "✏️ <b>Редактирование кейсов</b>\n\n"
        "Выберите кейс для изменения.",
        reply_markup=founder_cases_keyboard(),
    )


@router.callback_query(
    F.data == "founder:cases:rewards"
)
async def founder_cases_rewards(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🎲 <b>Награды кейсов</b>\n\n"
        "Здесь будет управление наградами, "
        "вероятностями и диапазонами выплат.",
        reply_markup=founder_cases_keyboard(),
    )


@router.callback_query(
    F.data == "founder:cases:delete"
)
async def founder_cases_delete(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🗑 <b>Удаление / отключение</b>\n\n"
        "Удаление кейса будет выполняться "
        "только после подтверждения Founder.",
        reply_markup=founder_cases_keyboard(),
    )