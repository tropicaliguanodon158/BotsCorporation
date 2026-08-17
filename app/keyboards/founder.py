from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ============================================================================
# FOUNDER MAIN PANEL
# ============================================================================


def founder_main_keyboard() -> InlineKeyboardMarkup:
    """
    Главное меню Founder Panel.

    Доступ к этому меню будет дополнительно проверяться
    FounderFilter'ом/handler'ом.

    Сама клавиатура не является механизмом безопасности.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="💰 Экономика",
        callback_data="founder:economy",
    )

    builder.button(
        text="👥 Пользователи",
        callback_data="founder:users",
    )

    builder.button(
        text="🏅 Ранги",
        callback_data="founder:ranks",
    )

    builder.button(
        text="✨ Способности",
        callback_data="founder:abilities",
    )

    builder.button(
        text="🧬 Расы",
        callback_data="founder:races",
    )

    builder.button(
        text="🛍 Магазин",
        callback_data="founder:shop",
    )

    builder.button(
        text="🎁 Кейсы",
        callback_data="founder:cases",
    )

    builder.button(
        text="🛡 Модерация",
        callback_data="founder:moderation",
    )

    builder.button(
        text="💬 Чаты",
        callback_data="founder:chats",
    )

    builder.button(
        text="⚙️ Система",
        callback_data="founder:system",
    )

    builder.button(
        text="📊 Статистика",
        callback_data="founder:statistics",
    )

    builder.button(
        text="❌ Закрыть",
        callback_data="founder:close",
    )

    builder.adjust(2, 2, 2, 2, 2, 1)

    return builder.as_markup()


# ============================================================================
# GENERIC BACK
# ============================================================================


def founder_back_keyboard(
    callback_data: str = "founder:main",
) -> InlineKeyboardMarkup:
    """
    Простая кнопка возврата.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🔙 Назад",
        callback_data=callback_data,
    )

    return builder.as_markup()


# ============================================================================
# ECONOMY
# ============================================================================


def founder_economy_keyboard() -> InlineKeyboardMarkup:
    """
    Управление экономикой.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🪙 Настройки валюты",
        callback_data="founder:economy:currency",
    )

    builder.button(
        text="💬 Награды за сообщения",
        callback_data="founder:economy:messages",
    )

    builder.button(
        text="🎁 Часовые награды",
        callback_data="founder:economy:rewards",
    )

    builder.button(
        text="🏦 Банк / депозит",
        callback_data="founder:economy:bank",
    )

    builder.button(
        text="⛏ Пассивный доход",
        callback_data="founder:economy:passive",
    )

    builder.button(
        text="🎮 Стоимость игр",
        callback_data="founder:economy:games",
    )

    builder.button(
        text="🤝 Стоимость взаимодействий",
        callback_data="founder:economy:interactions",
    )

    builder.button(
        text="💳 Кредиты",
        callback_data="founder:economy:credits",
    )

    builder.button(
        text="📈 Уровни экономики",
        callback_data="founder:economy:levels",
    )

    builder.button(
        text="📜 История операций",
        callback_data="founder:economy:transactions",
    )

    builder.button(
        text="🔙 Назад",
        callback_data="founder:main",
    )

    builder.adjust(2, 2, 2, 2, 2, 1)

    return builder.as_markup()


# ============================================================================
# ECONOMY SETTINGS
# ============================================================================


def founder_economy_settings_keyboard() -> InlineKeyboardMarkup:
    """
    Детальные настройки экономики.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✏️ Изменить значение",
        callback_data="founder:economy:edit",
    )

    builder.button(
        text="🔄 Сбросить настройки",
        callback_data="founder:economy:reset",
    )

    builder.button(
        text="📋 Показать текущие",
        callback_data="founder:economy:view",
    )

    builder.button(
        text="🔙 Экономика",
        callback_data="founder:economy",
    )

    builder.adjust(1)

    return builder.as_markup()


# ============================================================================
# USERS
# ============================================================================


def founder_users_keyboard() -> InlineKeyboardMarkup:
    """
    Управление пользователями.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🔎 Найти пользователя",
        callback_data="founder:users:search",
    )

    builder.button(
        text="👤 Пользователь по ID",
        callback_data="founder:users:id",
    )

    builder.button(
        text="👑 Управление правами",
        callback_data="founder:users:permissions",
    )

    builder.button(
        text="💰 Управление балансом",
        callback_data="founder:users:balance",
    )

    builder.button(
        text="⭐ Изменить XP / уровень",
        callback_data="founder:users:xp",
    )

    builder.button(
        text="🏅 Изменить ранг",
        callback_data="founder:users:rank",
    )

    builder.button(
        text="✨ Выдать способность",
        callback_data="founder:users:ability",
    )

    builder.button(
        text="🧬 Изменить расу",
        callback_data="founder:users:race",
    )

    builder.button(
        text="🎒 Управление инвентарём",
        callback_data="founder:users:inventory",
    )

    builder.button(
        text="🧹 Сбросить данные",
        callback_data="founder:users:reset",
    )

    builder.button(
        text="🔙 Назад",
        callback_data="founder:main",
    )

    builder.adjust(2, 2, 2, 2, 2, 1)

    return builder.as_markup()


# ============================================================================
# USER ACTIONS
# ============================================================================


def founder_user_actions_keyboard(
    user_id: int,
) -> InlineKeyboardMarkup:
    """
    Действия с конкретным пользователем.

    user_id используется только как идентификатор цели.
    Все права дополнительно проверяются handler/service.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="👤 Профиль",
        callback_data=f"founder:user:view:{user_id}",
    )

    builder.button(
        text="💰 Баланс",
        callback_data=f"founder:user:balance:{user_id}",
    )

    builder.button(
        text="⭐ XP / уровень",
        callback_data=f"founder:user:xp:{user_id}",
    )

    builder.button(
        text="🏅 Ранг",
        callback_data=f"founder:user:rank:{user_id}",
    )

    builder.button(
        text="✨ Способности",
        callback_data=f"founder:user:abilities:{user_id}",
    )

    builder.button(
        text="🎒 Инвентарь",
        callback_data=f"founder:user:inventory:{user_id}",
    )

    builder.button(
        text="🛡 Модерация",
        callback_data=f"founder:user:moderation:{user_id}",
    )

    builder.button(
        text="🚫 Заблокировать бота",
        callback_data=f"founder:user:disable:{user_id}",
    )

    builder.button(
        text="🔙 Пользователи",
        callback_data="founder:users",
    )

    builder.adjust(2, 2, 2, 1, 1)

    return builder.as_markup()


# ============================================================================
# RANKS
# ============================================================================


def founder_ranks_keyboard() -> InlineKeyboardMarkup:
    """
    Управление рангами персонажей.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📋 Список рангов",
        callback_data="founder:ranks:list:1",
    )

    builder.button(
        text="➕ Создать ранг",
        callback_data="founder:ranks:create",
    )

    builder.button(
        text="✏️ Редактировать",
        callback_data="founder:ranks:edit",
    )

    builder.button(
        text="📊 Порядок рангов",
        callback_data="founder:ranks:order",
    )

    builder.button(
        text="🗑 Удалить / отключить",
        callback_data="founder:ranks:delete",
    )

    builder.button(
        text="🔙 Назад",
        callback_data="founder:main",
    )

    builder.adjust(2, 2, 1, 1)

    return builder.as_markup()


def founder_rank_actions_keyboard(
    rank_id: int,
) -> InlineKeyboardMarkup:
    """
    Действия с конкретным рангом.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="👁 Просмотреть",
        callback_data=f"founder:rank:view:{rank_id}",
    )

    builder.button(
        text="✏️ Изменить",
        callback_data=f"founder:rank:edit:{rank_id}",
    )

    builder.button(
        text="📈 Бонусы характеристик",
        callback_data=f"founder:rank:stats:{rank_id}",
    )

    builder.button(
        text="🔓 Возможности ранга",
        callback_data=f"founder:rank:permissions:{rank_id}",
    )

    builder.button(
        text="🗑 Удалить",
        callback_data=f"founder:rank:delete:{rank_id}",
    )

    builder.button(
        text="🔙 Ранги",
        callback_data="founder:ranks",
    )

    builder.adjust(2, 2, 1, 1)

    return builder.as_markup()


# ============================================================================
# ABILITIES
# ============================================================================


def founder_abilities_keyboard() -> InlineKeyboardMarkup:
    """
    Управление игровыми способностями.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📋 Список способностей",
        callback_data="founder:abilities:list:1",
    )

    builder.button(
        text="➕ Создать способность",
        callback_data="founder:abilities:create",
    )

    builder.button(
        text="✏️ Редактировать",
        callback_data="founder:abilities:edit",
    )

    builder.button(
        text="🧩 Типы эффектов",
        callback_data="founder:abilities:types",
    )

    builder.button(
        text="🗑 Удалить / отключить",
        callback_data="founder:abilities:delete",
    )

    builder.button(
        text="🔙 Назад",
        callback_data="founder:main",
    )

    builder.adjust(2, 2, 1, 1)

    return builder.as_markup()


def founder_ability_actions_keyboard(
    ability_id: int,
) -> InlineKeyboardMarkup:
    """
    Действия с конкретной способностью.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="👁 Просмотреть",
        callback_data=f"founder:ability:view:{ability_id}",
    )

    builder.button(
        text="✏️ Изменить",
        callback_data=f"founder:ability:edit:{ability_id}",
    )

    builder.button(
        text="⏱ Cooldown",
        callback_data=f"founder:ability:cooldown:{ability_id}",
    )

    builder.button(
        text="✨ Выдать пользователю",
        callback_data=f"founder:ability:give:{ability_id}",
    )

    builder.button(
        text="🗑 Удалить",
        callback_data=f"founder:ability:delete:{ability_id}",
    )

    builder.button(
        text="🔙 Способности",
        callback_data="founder:abilities",
    )

    builder.adjust(2, 2, 1, 1)

    return builder.as_markup()


# ============================================================================
# RACES
# ============================================================================


def founder_races_keyboard() -> InlineKeyboardMarkup:
    """
    Управление расами.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📋 Список рас",
        callback_data="founder:races:list:1",
    )

    builder.button(
        text="➕ Создать расу",
        callback_data="founder:races:create",
    )

    builder.button(
        text="✏️ Редактировать",
        callback_data="founder:races:edit",
    )

    builder.button(
        text="📊 Характеристики",
        callback_data="founder:races:stats",
    )

    builder.button(
        text="🗑 Удалить / отключить",
        callback_data="founder:races:delete",
    )

    builder.button(
        text="🔙 Назад",
        callback_data="founder:main",
    )

    builder.adjust(2, 2, 1, 1)

    return builder.as_markup()


def founder_race_actions_keyboard(
    race_id: int,
) -> InlineKeyboardMarkup:
    """
    Действия с конкретной расой.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="👁 Просмотреть",
        callback_data=f"founder:race:view:{race_id}",
    )

    builder.button(
        text="✏️ Изменить",
        callback_data=f"founder:race:edit:{race_id}",
    )

    builder.button(
        text="📊 Характеристики",
        callback_data=f"founder:race:stats:{race_id}",
    )

    builder.button(
        text="🗑 Удалить",
        callback_data=f"founder:race:delete:{race_id}",
    )

    builder.button(
        text="🔙 Расы",
        callback_data="founder:races",
    )

    builder.adjust(2, 2, 1)

    return builder.as_markup()


# ============================================================================
# SHOP
# ============================================================================


def founder_shop_keyboard() -> InlineKeyboardMarkup:
    """
    Управление магазином.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📋 Список товаров",
        callback_data="founder:shop:list:1",
    )

    builder.button(
        text="➕ Создать товар",
        callback_data="founder:shop:create",
    )

    builder.button(
        text="✏️ Редактировать товар",
        callback_data="founder:shop:edit",
    )

    builder.button(
        text="💰 Изменить цены",
        callback_data="founder:shop:prices",
    )

    builder.button(
        text="📦 Остатки / наличие",
        callback_data="founder:shop:stock",
    )

    builder.button(
        text="🗑 Удалить / отключить",
        callback_data="founder:shop:delete",
    )

    builder.button(
        text="🔙 Назад",
        callback_data="founder:main",
    )

    builder.adjust(2, 2, 2, 1)

    return builder.as_markup()


def founder_item_actions_keyboard(
    item_id: int,
) -> InlineKeyboardMarkup:
    """
    Действия с конкретным предметом.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="👁 Просмотреть",
        callback_data=f"founder:item:view:{item_id}",
    )

    builder.button(
        text="✏️ Редактировать",
        callback_data=f"founder:item:edit:{item_id}",
    )

    builder.button(
        text="💰 Цена",
        callback_data=f"founder:item:price:{item_id}",
    )

    builder.button(
        text="📊 Характеристики",
        callback_data=f"founder:item:stats:{item_id}",
    )

    builder.button(
        text="🧪 Эффект",
        callback_data=f"founder:item:effect:{item_id}",
    )

    builder.button(
        text="🗑 Удалить",
        callback_data=f"founder:item:delete:{item_id}",
    )

    builder.button(
        text="🔙 Магазин",
        callback_data="founder:shop",
    )

    builder.adjust(2, 2, 2, 1)

    return builder.as_markup()


# ============================================================================
# CASES
# ============================================================================


def founder_cases_keyboard() -> InlineKeyboardMarkup:
    """
    Управление кейсами.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📋 Список кейсов",
        callback_data="founder:cases:list:1",
    )

    builder.button(
        text="➕ Создать кейс",
        callback_data="founder:cases:create",
    )

    builder.button(
        text="✏️ Редактировать кейс",
        callback_data="founder:cases:edit",
    )

    builder.button(
        text="🎁 Содержимое кейсов",
        callback_data="founder:cases:contents",
    )

    builder.button(
        text="🎲 Шансы выпадения",
        callback_data="founder:cases:odds",
    )

    builder.button(
        text="💰 Стоимость",
        callback_data="founder:cases:prices",
    )

    builder.button(
        text="🗑 Удалить / отключить",
        callback_data="founder:cases:delete",
    )

    builder.button(
        text="🔙 Назад",
        callback_data="founder:main",
    )

    builder.adjust(2, 2, 2, 1)

    return builder.as_markup()


# ============================================================================
# MODERATION
# ============================================================================


def founder_moderation_keyboard() -> InlineKeyboardMarkup:
    """
    Глобальная настройка модерации.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🛡 Настройки модерации",
        callback_data="founder:moderation:settings",
    )

    builder.button(
        text="🚫 Фильтры",
        callback_data="founder:moderation:filters",
    )

    builder.button(
        text="⚠️ Предупреждения",
        callback_data="founder:moderation:warnings",
    )

    builder.button(
        text="🔇 Муты",
        callback_data="founder:moderation:mutes",
    )

    builder.button(
        text="🔨 Баны",
        callback_data="founder:moderation:bans",
    )

    builder.button(
        text="👮 Уровни модераторов",
        callback_data="founder:moderation:levels",
    )

    builder.button(
        text="📜 История наказаний",
        callback_data="founder:moderation:history",
    )

    builder.button(
        text="🔙 Назад",
        callback_data="founder:main",
    )

    builder.adjust(2, 2, 2, 1)

    return builder.as_markup()


# ============================================================================
# CHATS
# ============================================================================


def founder_chats_keyboard() -> InlineKeyboardMarkup:
    """
    Управление чатами, подключенными к боту.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📋 Мои чаты",
        callback_data="founder:chats:list",
    )

    builder.button(
        text="➕ Добавить чат",
        callback_data="founder:chats:add",
    )

    builder.button(
        text="⚙️ Настройки чата",
        callback_data="founder:chats:settings",
    )

    builder.button(
        text="💰 Экономика чата",
        callback_data="founder:chats:economy",
    )

    builder.button(
        text="🛡 Модерация чата",
        callback_data="founder:chats:moderation",
    )

    builder.button(
        text="🎮 Игры чата",
        callback_data="founder:chats:games",
    )

    builder.button(
        text="🧬 Персонажи чата",
        callback_data="founder:chats:characters",
    )

    builder.button(
        text="📊 Статистика чата",
        callback_data="founder:chats:statistics",
    )

    builder.button(
        text="🔙 Назад",
        callback_data="founder:main",
    )

    builder.adjust(2, 2, 2, 2, 1)

    return builder.as_markup()


# ============================================================================
# CHAT SETTINGS
# ============================================================================


def founder_chat_settings_keyboard(
    chat_id: int,
) -> InlineKeyboardMarkup:
    """
    Настройки конкретного чата.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="💰 Экономика",
        callback_data=f"founder:chat:economy:{chat_id}",
    )

    builder.button(
        text="🛡 Модерация",
        callback_data=f"founder:chat:moderation:{chat_id}",
    )

    builder.button(
        text="🎮 Игры",
        callback_data=f"founder:chat:games:{chat_id}",
    )

    builder.button(
        text="🤝 Взаимодействия",
        callback_data=f"founder:chat:interactions:{chat_id}",
    )

    builder.button(
        text="🧬 Персонажи",
        callback_data=f"founder:chat:characters:{chat_id}",
    )

    builder.button(
        text="🎁 Награды",
        callback_data=f"founder:chat:rewards:{chat_id}",
    )

    builder.button(
        text="👋 Приветствие",
        callback_data=f"founder:chat:welcome:{chat_id}",
    )

    builder.button(
        text="📝 Логи",
        callback_data=f"founder:chat:logging:{chat_id}",
    )

    builder.button(
        text="🌐 Язык / часовой пояс",
        callback_data=f"founder:chat:localization:{chat_id}",
    )

    builder.button(
        text="🔙 Чаты",
        callback_data="founder:chats",
    )

    builder.adjust(2, 2, 2, 2, 1)

    return builder.as_markup()


# ============================================================================
# SYSTEM
# ============================================================================


def founder_system_keyboard() -> InlineKeyboardMarkup:
    """
    Системные настройки.

    Здесь будут параметры, которые не относятся
    непосредственно к конкретному чату.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="👑 Основатель",
        callback_data="founder:system:founder",
    )

    builder.button(
        text="🔐 Права доступа",
        callback_data="founder:system:permissions",
    )

    builder.button(
        text="⚙️ Глобальные настройки",
        callback_data="founder:system:settings",
    )

    builder.button(
        text="📊 Статистика",
        callback_data="founder:statistics",
    )

    builder.button(
        text="🧹 Очистка данных",
        callback_data="founder:system:cleanup",
    )

    builder.button(
        text="🔄 Системная информация",
        callback_data="founder:system:info",
    )

    builder.button(
        text="🔙 Назад",
        callback_data="founder:main",
    )

    builder.adjust(2, 2, 2, 1)

    return builder.as_markup()


# ============================================================================
# CONFIRMATION
# ============================================================================


def founder_confirm_keyboard(
    action: str,
    target_id: int | str,
    *,
    cancel_callback: str = "founder:main",
) -> InlineKeyboardMarkup:
    """
    Универсальное подтверждение опасного действия.

    Например:

        founder_confirm_keyboard("delete_item", 15)

    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Подтвердить",
        callback_data=f"founder:confirm:{action}:{target_id}",
    )

    builder.button(
        text="❌ Отмена",
        callback_data=cancel_callback,
    )

    builder.adjust(2)

    return builder.as_markup()


# ============================================================================
# PAGINATION
# ============================================================================


def founder_pagination_keyboard(
    prefix: str,
    page: int,
    *,
    has_previous: bool = False,
    has_next: bool = False,
    back_callback: str = "founder:main",
) -> InlineKeyboardMarkup:
    """
    Универсальная пагинация Founder Panel.

    prefix:

        users
        ranks
        abilities
        races
        shop
        cases

    """

    builder = InlineKeyboardBuilder()

    if has_previous:
        builder.button(
            text="⬅️",
            callback_data=f"founder:{prefix}:list:{page - 1}",
        )

    if has_next:
        builder.button(
            text="➡️",
            callback_data=f"founder:{prefix}:list:{page + 1}",
        )

    if has_previous or has_next:
        builder.adjust(2)

    builder.button(
        text="🔙 Назад",
        callback_data=back_callback,
    )

    return builder.as_markup()


# ============================================================================
# YES / NO
# ============================================================================


def founder_yes_no_keyboard(
    yes_callback: str,
    no_callback: str,
) -> InlineKeyboardMarkup:
    """
    Универсальная клавиатура Да / Нет.
    """

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Да",
        callback_data=yes_callback,
    )

    builder.button(
        text="❌ Нет",
        callback_data=no_callback,
    )

    builder.adjust(2)

    return builder.as_markup()