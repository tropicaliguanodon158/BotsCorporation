from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ============================================================================
# SHOP MAIN
# ============================================================================


def shop_keyboard() -> InlineKeyboardMarkup:
    """
    Главное меню магазина.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🛍 Все товары",
        callback_data="shop:list:all:1",
    )

    builder.button(
        text="⚔️ Оружие",
        callback_data="shop:list:weapon:1",
    )

    builder.button(
        text="🛡 Броня",
        callback_data="shop:list:armor:1",
    )

    builder.button(
        text="💍 Аксессуары",
        callback_data="shop:list:accessory:1",
    )

    builder.button(
        text="🎨 Косметика",
        callback_data="shop:list:cosmetic:1",
    )

    builder.button(
        text="🧪 Расходники",
        callback_data="shop:list:consumable:1",
    )

    builder.button(
        text="🎁 Кейсы",
        callback_data="shop:list:case:1",
    )

    builder.button(
        text="🎒 Мой инвентарь",
        callback_data="shop:inventory",
    )

    builder.button(
        text="🔙 Главное меню",
        callback_data="menu:main",
    )

    builder.adjust(2, 2, 2, 1, 1)

    return builder.as_markup()


# ============================================================================
# SHOP CATEGORY
# ============================================================================


def shop_category_keyboard(
    item_type: str,
    page: int = 1,
    *,
    has_previous: bool = False,
    has_next: bool = False,
) -> InlineKeyboardMarkup:
    """
    Навигация внутри категории магазина.

    item_type:
        all
        weapon
        armor
        accessory
        cosmetic
        consumable
        case
        и другие типы, которые появятся позднее.
    """

    builder = InlineKeyboardBuilder()

    if has_previous:
        builder.button(
            text="⬅️",
            callback_data=f"shop:list:{item_type}:{page - 1}",
        )

    if has_next:
        builder.button(
            text="➡️",
            callback_data=f"shop:list:{item_type}:{page + 1}",
        )

    if has_previous or has_next:
        builder.adjust(2)

    builder.button(
        text="🛍 Категории",
        callback_data="shop:main",
    )

    builder.button(
        text="🎒 Инвентарь",
        callback_data="shop:inventory",
    )

    builder.button(
        text="🔙 Главное меню",
        callback_data="menu:main",
    )

    builder.adjust(2, 1)

    return builder.as_markup()


# ============================================================================
# ITEM
# ============================================================================


def item_keyboard(
    item_id: int,
    *,
    can_buy: bool = True,
    can_sell: bool = False,
    can_equip: bool = False,
    can_use: bool = False,
    can_trade: bool = False,
    back_callback: str = "shop:main",
) -> InlineKeyboardMarkup:
    """
    Действия с конкретным предметом.

    Параметры can_* позволяют сервису/handler'у
    показать только допустимые действия.
    """

    builder = InlineKeyboardBuilder()

    if can_buy:
        builder.button(
            text="🛒 Купить",
            callback_data=f"shop:buy:{item_id}",
        )

    if can_sell:
        builder.button(
            text="💰 Продать",
            callback_data=f"shop:sell:{item_id}",
        )

    if can_equip:
        builder.button(
            text="⚔️ Экипировать",
            callback_data=f"shop:equip:{item_id}",
        )

    if can_use:
        builder.button(
            text="🧪 Использовать",
            callback_data=f"shop:use:{item_id}",
        )

    if can_trade:
        builder.button(
            text="🔄 Передать",
            callback_data=f"shop:trade:{item_id}",
        )

    builder.button(
        text="🔙 Назад",
        callback_data=back_callback,
    )

    builder.adjust(2, 2, 1)

    return builder.as_markup()


# ============================================================================
# BUY CONFIRMATION
# ============================================================================


def buy_confirmation_keyboard(
    item_id: int,
) -> InlineKeyboardMarkup:
    """
    Подтверждение покупки предмета.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Купить",
        callback_data=f"shop:buy:confirm:{item_id}",
    )

    builder.button(
        text="❌ Отмена",
        callback_data=f"shop:item:{item_id}",
    )

    builder.adjust(2)

    return builder.as_markup()


# ============================================================================
# SELL CONFIRMATION
# ============================================================================


def sell_confirmation_keyboard(
    item_id: int,
) -> InlineKeyboardMarkup:
    """
    Подтверждение продажи предмета.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Продать",
        callback_data=f"shop:sell:confirm:{item_id}",
    )

    builder.button(
        text="❌ Отмена",
        callback_data=f"shop:item:{item_id}",
    )

    builder.adjust(2)

    return builder.as_markup()


# ============================================================================
# QUANTITY
# ============================================================================


def quantity_keyboard(
    *,
    action: str,
    item_id: int,
    quantity: int = 1,
    max_quantity: int = 99,
) -> InlineKeyboardMarkup:
    """
    Выбор количества предметов.

    action:
        buy
        sell
        use
        trade
    """

    builder = InlineKeyboardBuilder()

    if quantity > 1:
        builder.button(
            text="➖",
            callback_data=(
                f"shop:quantity:{action}:{item_id}:{quantity - 1}"
            ),
        )

    builder.button(
        text=f"× {quantity}",
        callback_data="shop:quantity:noop",
    )

    if quantity < max_quantity:
        builder.button(
            text="➕",
            callback_data=(
                f"shop:quantity:{action}:{item_id}:{quantity + 1}"
            ),
        )

    builder.button(
        text="✅ Подтвердить",
        callback_data=(
            f"shop:quantity:confirm:"
            f"{action}:{item_id}:{quantity}"
        ),
    )

    builder.button(
        text="❌ Отмена",
        callback_data=f"shop:item:{item_id}",
    )

    builder.adjust(3, 2)

    return builder.as_markup()


# ============================================================================
# INVENTORY
# ============================================================================


def inventory_keyboard(
    *,
    page: int = 1,
    has_previous: bool = False,
    has_next: bool = False,
) -> InlineKeyboardMarkup:
    """
    Главное меню инвентаря.
    """

    builder = InlineKeyboardBuilder()

    if has_previous:
        builder.button(
            text="⬅️",
            callback_data=f"inventory:list:{page - 1}",
        )

    if has_next:
        builder.button(
            text="➡️",
            callback_data=f"inventory:list:{page + 1}",
        )

    if has_previous or has_next:
        builder.adjust(2)

    builder.button(
        text="⚔️ Экипировка",
        callback_data="inventory:equipment",
    )

    builder.button(
        text="🛍 Магазин",
        callback_data="shop:main",
    )

    builder.button(
        text="🔙 Главное меню",
        callback_data="menu:main",
    )

    builder.adjust(2, 1)

    return builder.as_markup()


# ============================================================================
# INVENTORY ITEM
# ============================================================================


def inventory_item_keyboard(
    item_id: int,
    *,
    can_equip: bool = False,
    can_use: bool = False,
    can_sell: bool = False,
    can_trade: bool = False,
) -> InlineKeyboardMarkup:
    """
    Действия с предметом из инвентаря.
    """

    builder = InlineKeyboardBuilder()

    if can_equip:
        builder.button(
            text="⚔️ Экипировать",
            callback_data=f"inventory:equip:{item_id}",
        )

    if can_use:
        builder.button(
            text="🧪 Использовать",
            callback_data=f"inventory:use:{item_id}",
        )

    if can_sell:
        builder.button(
            text="💰 Продать",
            callback_data=f"inventory:sell:{item_id}",
        )

    if can_trade:
        builder.button(
            text="🔄 Передать",
            callback_data=f"inventory:trade:{item_id}",
        )

    builder.button(
        text="🔙 Инвентарь",
        callback_data="shop:inventory",
    )

    builder.adjust(2, 2, 1)

    return builder.as_markup()


# ============================================================================
# EQUIPMENT
# ============================================================================


def equipment_keyboard(
    equipped_slots: dict[str, int | None] | None = None,
) -> InlineKeyboardMarkup:
    """
    Меню экипировки.

    equipped_slots может содержать:

        {
            "weapon": 123,
            "armor": 456,
            "accessory": None,
        }

    Значения ID используются только для отображения состояния.
    """

    equipped_slots = equipped_slots or {}

    builder = InlineKeyboardBuilder()

    weapon_text = (
        "⚔️ Оружие"
        if equipped_slots.get("weapon") is None
        else "⚔️ Оружие: экипировано"
    )

    armor_text = (
        "🛡 Броня"
        if equipped_slots.get("armor") is None
        else "🛡 Броня: экипирована"
    )

    accessory_text = (
        "💍 Аксессуар"
        if equipped_slots.get("accessory") is None
        else "💍 Аксессуар: экипирован"
    )

    builder.button(
        text=weapon_text,
        callback_data="inventory:equipment:weapon",
    )

    builder.button(
        text=armor_text,
        callback_data="inventory:equipment:armor",
    )

    builder.button(
        text=accessory_text,
        callback_data="inventory:equipment:accessory",
    )

    builder.button(
        text="🧹 Снять экипировку",
        callback_data="inventory:equipment:unequip",
    )

    builder.button(
        text="🔙 Инвентарь",
        callback_data="shop:inventory",
    )

    builder.adjust(2, 1, 1)

    return builder.as_markup()