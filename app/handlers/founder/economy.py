from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.filters.founder import FounderFilter
from app.keyboards.founder import (
    founder_economy_keyboard,
    founder_economy_settings_keyboard,
)

router = Router(name="founder_economy")
router.callback_query.filter(FounderFilter())


@router.callback_query(F.data == "founder:economy")
async def founder_economy(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "💰 <b>Экономика</b>\n\n"
        "Выберите раздел управления экономикой.",
        reply_markup=founder_economy_keyboard(),
    )


@router.callback_query(F.data == "founder:economy:currency")
async def founder_currency(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🪙 <b>Настройки валюты</b>\n\n"
        "Здесь будут настраиваться название валюты, "
        "символ и базовые параметры.",
        reply_markup=founder_economy_settings_keyboard(),
    )


@router.callback_query(F.data == "founder:economy:messages")
async def founder_message_rewards(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "💬 <b>Награды за сообщения</b>\n\n"
        "Настройка начислений за сообщения будет подключена "
        "к SettingsRepository.",
        reply_markup=founder_economy_settings_keyboard(),
    )


@router.callback_query(F.data == "founder:economy:rewards")
async def founder_hourly_rewards(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🎁 <b>Часовые награды</b>\n\n"
        "Настройка периодических наград.",
        reply_markup=founder_economy_settings_keyboard(),
    )


@router.callback_query(F.data == "founder:economy:bank")
async def founder_bank(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🏦 <b>Банк / депозит</b>\n\n"
        "Настройки банковской системы.",
        reply_markup=founder_economy_settings_keyboard(),
    )


@router.callback_query(F.data == "founder:economy:passive")
async def founder_passive_income(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "⛏ <b>Пассивный доход</b>\n\n"
        "Настройки депозитов, майнинга и требований активности.",
        reply_markup=founder_economy_settings_keyboard(),
    )


@router.callback_query(F.data == "founder:economy:games")
async def founder_game_prices(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🎮 <b>Стоимость игр</b>\n\n"
        "Здесь будут настраиваться цены игровых действий.",
        reply_markup=founder_economy_settings_keyboard(),
    )


@router.callback_query(F.data == "founder:economy:interactions")
async def founder_interaction_prices(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🤝 <b>Стоимость взаимодействий</b>\n\n"
        "Настройки стоимости команд взаимодействия.",
        reply_markup=founder_economy_settings_keyboard(),
    )


@router.callback_query(F.data == "founder:economy:credits")
async def founder_credits(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "💳 <b>Кредиты</b>\n\n"
        "Настройки кредитной системы.",
        reply_markup=founder_economy_settings_keyboard(),
    )


@router.callback_query(F.data == "founder:economy:levels")
async def founder_economy_levels(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "📈 <b>Уровни экономики</b>\n\n"
        "Настройки прогрессии экономики.",
        reply_markup=founder_economy_settings_keyboard(),
    )


@router.callback_query(F.data == "founder:economy:transactions")
async def founder_transactions(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "📜 <b>История операций</b>\n\n"
        "Просмотр финансовых транзакций.",
        reply_markup=founder_economy_settings_keyboard(),
    )


@router.callback_query(F.data == "founder:economy:view")
async def founder_economy_view(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "📋 <b>Текущие настройки</b>\n\n"
        "Значения будут загружаться из SettingsRepository.",
        reply_markup=founder_economy_settings_keyboard(),
    )


@router.callback_query(F.data == "founder:economy:edit")
async def founder_economy_edit(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "✏️ <b>Изменение настройки</b>\n\n"
        "Ввод параметров через FSM подключим следующим этапом.",
        reply_markup=founder_economy_settings_keyboard(),
    )


@router.callback_query(F.data == "founder:economy:reset")
async def founder_economy_reset(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🔄 <b>Сброс настроек</b>\n\n"
        "Защищённый сброс настроек подключим через сервис.",
        reply_markup=founder_economy_settings_keyboard(),
    )