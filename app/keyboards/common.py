from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ============================================================================
# MAIN MENU
# ============================================================================


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Главное меню бота.

    Используется в /start и других местах,
    где пользователю нужно показать основные разделы.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="👤 Профиль",
        callback_data="menu:profile",
    )

    builder.button(
        text="💰 Экономика",
        callback_data="menu:economy",
    )

    builder.button(
        text="🎮 Игры",
        callback_data="menu:games",
    )

    builder.button(
        text="🧙 Персонаж",
        callback_data="menu:character",
    )

    builder.button(
        text="🎒 Инвентарь",
        callback_data="menu:inventory",
    )

    builder.button(
        text="🏆 Достижения",
        callback_data="menu:achievements",
    )

    builder.button(
        text="📜 Квесты",
        callback_data="menu:quests",
    )

    builder.button(
        text="❓ Помощь",
        callback_data="menu:help",
    )

    builder.adjust(2, 2, 2, 2)

    return builder.as_markup()


# ============================================================================
# HELP
# ============================================================================


def help_keyboard() -> InlineKeyboardMarkup:
    """
    Меню справки.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="💰 Экономика",
        callback_data="help:economy",
    )

    builder.button(
        text="🎮 Игры",
        callback_data="help:games",
    )

    builder.button(
        text="🧙 Персонаж",
        callback_data="help:character",
    )

    builder.button(
        text="🛡 Модерация",
        callback_data="help:moderation",
    )

    builder.button(
        text="🏆 Ранги",
        callback_data="help:ranks",
    )

    builder.button(
        text="🎒 Инвентарь",
        callback_data="help:inventory",
    )

    builder.button(
        text="🔙 Главное меню",
        callback_data="menu:main",
    )

    builder.adjust(2, 2, 2, 1)

    return builder.as_markup()


# ============================================================================
# PROFILE
# ============================================================================


def profile_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопки профиля пользователя.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🧙 Персонаж",
        callback_data="profile:character",
    )

    builder.button(
        text="🎒 Инвентарь",
        callback_data="profile:inventory",
    )

    builder.button(
        text="💰 Баланс",
        callback_data="profile:balance",
    )

    builder.button(
        text="🏆 Достижения",
        callback_data="profile:achievements",
    )

    builder.button(
        text="📜 Квесты",
        callback_data="profile:quests",
    )

    builder.button(
        text="🔙 Главное меню",
        callback_data="menu:main",
    )

    builder.adjust(2, 2, 1, 1)

    return builder.as_markup()


# ============================================================================
# BACK BUTTON
# ============================================================================


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    """
    Простая кнопка возврата в главное меню.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🔙 Главное меню",
        callback_data="menu:main",
    )

    return builder.as_markup()


# ============================================================================
# CONFIRMATION
# ============================================================================


def confirmation_keyboard(
    confirm_callback: str,
    cancel_callback: str,
    *,
    confirm_text: str = "✅ Подтвердить",
    cancel_text: str = "❌ Отмена",
) -> InlineKeyboardMarkup:
    """
    Универсальная клавиатура подтверждения.

    Используется для потенциально опасных операций:

        покупка;
        продажа;
        сброс;
        удаление;
        выдача предмета;
        изменение настроек Founder Panel.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text=confirm_text,
        callback_data=confirm_callback,
    )

    builder.button(
        text=cancel_text,
        callback_data=cancel_callback,
    )

    builder.adjust(2)

    return builder.as_markup()


# ============================================================================
# PAGINATION
# ============================================================================


def pagination_keyboard(
    *,
    previous_callback: str | None = None,
    next_callback: str | None = None,
    back_callback: str = "menu:main",
) -> InlineKeyboardMarkup:
    """
    Универсальная пагинация.

    Кнопки создаются только если соответствующий callback
    передан.

    Пример:

        pagination_keyboard(
            previous_callback="page:previous",
            next_callback="page:next",
        )
    """

    builder = InlineKeyboardBuilder()

    if previous_callback is not None:
        builder.button(
            text="⬅️",
            callback_data=previous_callback,
        )

    if next_callback is not None:
        builder.button(
            text="➡️",
            callback_data=next_callback,
        )

    builder.button(
        text="🔙 Назад",
        callback_data=back_callback,
    )

    if previous_callback and next_callback:
        builder.adjust(2, 1)
    else:
        builder.adjust(1, 1)

    return builder.as_markup()