from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.filters.founder import FounderFilter
from app.keyboards.founder import founder_back_keyboard

router = Router(name="founder_shop")
router.callback_query.filter(FounderFilter())


@router.callback_query(F.data == "founder:shop")
async def founder_shop(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🛍 <b>Магазин</b>\n\n"
        "Управление товарами, ценами и категориями магазина.",
        reply_markup=founder_back_keyboard("founder:main"),
    )


@router.callback_query(F.data.startswith("founder:shop:"))
async def founder_shop_action(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.edit_text(
        "🛍 <b>Магазин</b>\n\n"
        f"Выбрано действие: <code>{callback.data}</code>\n\n"
        "Конкретные операции магазина подключим "
        "к InventoryService.",
        reply_markup=founder_back_keyboard("founder:shop"),
    )