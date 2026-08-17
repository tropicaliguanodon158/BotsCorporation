from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ============================================================================
# PROFILE
# ============================================================================


def profile_keyboard() -> InlineKeyboardMarkup:
    """
    Основное меню профиля пользователя.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🧙 Персонаж",
        callback_data="profile:character",
    )

    builder.button(
        text="💰 Баланс",
        callback_data="profile:balance",
    )

    builder.button(
        text="🎒 Инвентарь",
        callback_data="profile:inventory",
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
        text="📊 Статистика",
        callback_data="profile:statistics",
    )

    builder.button(
        text="🔙 Главное меню",
        callback_data="menu:main",
    )

    builder.adjust(2, 2, 2, 1)

    return builder.as_markup()


# ============================================================================
# PROFILE ACTIONS
# ============================================================================


def profile_actions_keyboard() -> InlineKeyboardMarkup:
    """
    Дополнительные действия с профилем.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✏️ Изменить профиль",
        callback_data="profile:edit",
    )

    builder.button(
        text="🧙 Настроить персонажа",
        callback_data="profile:character:edit",
    )

    builder.button(
        text="🎨 Кастомизация",
        callback_data="profile:customization",
    )

    builder.button(
        text="🔙 Назад",
        callback_data="profile:main",
    )

    builder.adjust(2, 1)

    return builder.as_markup()


# ============================================================================
# PROFILE EDIT
# ============================================================================


def profile_edit_keyboard() -> InlineKeyboardMarkup:
    """
    Меню редактирования пользовательского профиля.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✏️ Имя",
        callback_data="profile:edit:name",
    )

    builder.button(
        text="📝 Описание",
        callback_data="profile:edit:bio",
    )

    builder.button(
        text="🎨 Кастомизация",
        callback_data="profile:customization",
    )

    builder.button(
        text="🔙 Назад",
        callback_data="profile:main",
    )

    builder.adjust(2, 1, 1)

    return builder.as_markup()


# ============================================================================
# PROFILE STATISTICS
# ============================================================================


def profile_statistics_keyboard() -> InlineKeyboardMarkup:
    """
    Меню статистики пользователя.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="💰 Экономика",
        callback_data="statistics:economy",
    )

    builder.button(
        text="🎮 Игры",
        callback_data="statistics:games",
    )

    builder.button(
        text="💬 Активность",
        callback_data="statistics:activity",
    )

    builder.button(
        text="🧙 Персонаж",
        callback_data="statistics:character",
    )

    builder.button(
        text="🔙 Назад",
        callback_data="profile:main",
    )

    builder.adjust(2, 2, 1)

    return builder.as_markup()


# ============================================================================
# PROFILE VIEW OTHER USER
# ============================================================================


def user_profile_keyboard(
    user_id: int,
) -> InlineKeyboardMarkup:
    """
    Клавиатура при просмотре профиля другого пользователя.

    user_id используется только для формирования callback_data.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🧙 Персонаж",
        callback_data=f"user:{user_id}:character",
    )

    builder.button(
        text="🎒 Инвентарь",
        callback_data=f"user:{user_id}:inventory",
    )

    builder.button(
        text="🏆 Достижения",
        callback_data=f"user:{user_id}:achievements",
    )

    builder.button(
        text="🎭 Взаимодействие",
        callback_data=f"interaction:{user_id}:menu",
    )

    builder.button(
        text="🔙 Назад",
        callback_data="menu:main",
    )

    builder.adjust(2, 2, 1)

    return builder.as_markup()