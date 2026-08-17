from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.filters.founder import FounderFilter
from app.keyboards.founder import (
    founder_users_keyboard,
)

router = Router(name="founder_users")
router.callback_query.filter(FounderFilter())


@router.callback_query(F.data == "founder:users")
async def founder_users(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "👥 <b>Пользователи</b>\n\n"
        "Управление пользователями бота.",
        reply_markup=founder_users_keyboard(),
    )


@router.callback_query(
    F.data == "founder:users:search"
)
async def founder_users_search(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🔎 <b>Поиск пользователя</b>\n\n"
        "Введите Telegram ID или username "
        "пользователя.",
        reply_markup=founder_users_keyboard(),
    )


@router.callback_query(
    F.data == "founder:users:id"
)
async def founder_users_by_id(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "👤 <b>Пользователь по ID</b>\n\n"
        "Введите Telegram ID пользователя.",
        reply_markup=founder_users_keyboard(),
    )


@router.callback_query(
    F.data == "founder:users:permissions"
)
async def founder_users_permissions(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "👑 <b>Управление правами</b>\n\n"
        "Здесь будет управление Founder, "
        "администраторами и другими ролями.",
        reply_markup=founder_users_keyboard(),
    )


@router.callback_query(
    F.data == "founder:users:balance"
)
async def founder_users_balance(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "💰 <b>Управление балансом</b>\n\n"
        "Здесь можно будет начислять и списывать "
        "валюту пользователям.",
        reply_markup=founder_users_keyboard(),
    )


@router.callback_query(
    F.data == "founder:users:xp"
)
async def founder_users_xp(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "⭐ <b>XP / уровень</b>\n\n"
        "Здесь будет управление XP и уровнем "
        "пользователя.",
        reply_markup=founder_users_keyboard(),
    )


@router.callback_query(
    F.data == "founder:users:rank"
)
async def founder_users_rank(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🏅 <b>Изменение ранга</b>\n\n"
        "Здесь будет изменение ранга персонажа.",
        reply_markup=founder_users_keyboard(),
    )


@router.callback_query(
    F.data == "founder:users:ability"
)
async def founder_users_ability(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "✨ <b>Выдача способности</b>\n\n"
        "Здесь Founder сможет выдать "
        "способность пользователю.",
        reply_markup=founder_users_keyboard(),
    )


@router.callback_query(
    F.data == "founder:users:race"
)
async def founder_users_race(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🧬 <b>Изменение расы</b>\n\n"
        "Здесь будет изменение расы персонажа.",
        reply_markup=founder_users_keyboard(),
    )


@router.callback_query(
    F.data == "founder:users:inventory"
)
async def founder_users_inventory(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🎒 <b>Управление инвентарём</b>\n\n"
        "Здесь будет управление предметами "
        "пользователя.",
        reply_markup=founder_users_keyboard(),
    )


@router.callback_query(
    F.data == "founder:users:reset"
)
async def founder_users_reset(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🧹 <b>Сброс данных</b>\n\n"
        "Опасные операции будут доступны "
        "только после отдельного подтверждения.",
        reply_markup=founder_users_keyboard(),
    )