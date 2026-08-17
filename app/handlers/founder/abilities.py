from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.filters.founder import FounderFilter
from app.keyboards.founder import (
    founder_abilities_keyboard,
)

router = Router(name="founder_abilities")
router.callback_query.filter(FounderFilter())


@router.callback_query(F.data == "founder:abilities")
async def founder_abilities(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "✨ <b>Способности</b>\n\n"
        "Управление RPG-способностями персонажей.",
        reply_markup=founder_abilities_keyboard(),
    )


@router.callback_query(
    F.data == "founder:abilities:list:1"
)
async def founder_abilities_list(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "📋 <b>Список способностей</b>\n\n"
        "Список будет загружаться из "
        "CharacterRepository.",
        reply_markup=founder_abilities_keyboard(),
    )


@router.callback_query(
    F.data == "founder:abilities:create"
)
async def founder_abilities_create(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "➕ <b>Создание способности</b>\n\n"
        "FSM-форма создания способности "
        "будет подключена следующим этапом.",
        reply_markup=founder_abilities_keyboard(),
    )


@router.callback_query(
    F.data == "founder:abilities:edit"
)
async def founder_abilities_edit(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "✏️ <b>Редактирование способностей</b>\n\n"
        "Выберите способность для изменения.",
        reply_markup=founder_abilities_keyboard(),
    )


@router.callback_query(
    F.data == "founder:abilities:types"
)
async def founder_abilities_types(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🧩 <b>Типы эффектов</b>\n\n"
        "Здесь будут доступны типы эффектов "
        "и их параметры.",
        reply_markup=founder_abilities_keyboard(),
    )


@router.callback_query(
    F.data == "founder:abilities:delete"
)
async def founder_abilities_delete(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🗑 <b>Удаление / отключение</b>\n\n"
        "Удаление способности будет выполняться "
        "только после подтверждения Founder.",
        reply_markup=founder_abilities_keyboard(),
    )