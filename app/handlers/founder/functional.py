from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.admin import (
    AdminLevel,
    ChatAdmin,
    Permission,
)
from app.database.models.cases import Case, CaseReward
from app.database.models.character import (
    Ability,
    Character,
    CharacterAbility,
    CharacterRank,
    Race,
)
from app.database.models.chat import Chat
from app.database.models.economy import Transaction, Wallet
from app.database.models.inventory import Item
from app.database.models.user import User
from app.database.repositories.characters import CharacterRepository
from app.database.repositories.economy import EconomyRepository
from app.database.repositories.inventory import InventoryRepository
from app.database.repositories.settings import SettingsRepository
from app.database.repositories.users import UserRepository
from app.filters.founder import FounderFilter
from app.keyboards.founder import (
    founder_abilities_keyboard,
    founder_ability_actions_keyboard,
    founder_back_keyboard,
    founder_cases_keyboard,
    founder_chats_keyboard,
    founder_chat_settings_keyboard,
    founder_economy_keyboard,
    founder_economy_settings_keyboard,
    founder_item_actions_keyboard,
    founder_main_keyboard,
    founder_moderation_keyboard,
    founder_race_actions_keyboard,
    founder_races_keyboard,
    founder_rank_actions_keyboard,
    founder_ranks_keyboard,
    founder_shop_keyboard,
    founder_system_keyboard,
    founder_user_actions_keyboard,
    founder_users_keyboard,
)


router = Router(name="founder_functional")

router.callback_query.filter(FounderFilter())
router.message.filter(FounderFilter())


# ============================================================================
# FSM
# ============================================================================


class FounderStates(StatesGroup):
    target_chat = State()

    setting = State()

    user_lookup = State()
    user_balance = State()
    user_xp = State()
    user_level = State()
    user_rank = State()
    user_race = State()
    user_ability = State()
    user_inventory = State()

    create_race = State()
    edit_race = State()

    create_rank = State()
    edit_rank = State()

    create_ability = State()
    edit_ability = State()

    create_item = State()
    edit_item = State()

    create_case = State()
    edit_case = State()


# ============================================================================
# HELPERS
# ============================================================================


def _repositories(
    session: AsyncSession,
) -> tuple[
    UserRepository,
    EconomyRepository,
    SettingsRepository,
    CharacterRepository,
    InventoryRepository,
]:
    return (
        UserRepository(session),
        EconomyRepository(session),
        SettingsRepository(session),
        CharacterRepository(session),
        InventoryRepository(session),
    )


async def _target_chat(
    state: FSMContext,
) -> int | None:
    data = await state.get_data()

    value = data.get("target_chat_id")

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


async def _require_target_chat(
    callback: CallbackQuery,
    state: FSMContext,
) -> int | None:
    chat_id = await _target_chat(state)

    if chat_id is None:
        await callback.answer(
            "Сначала выбери чат.",
            show_alert=True,
        )

        if callback.message is not None:
            await callback.message.edit_text(
                "💬 <b>Чат не выбран</b>\n\n"
                "Сначала открой раздел «Чаты» и добавь "
                "или выбери Telegram chat ID.",
                reply_markup=founder_chats_keyboard(),
            )

        return None

    return chat_id


async def _edit(
    callback: CallbackQuery,
    text: str,
    reply_markup=None,
) -> None:
    await callback.answer()

    if callback.message is None:
        return

    await callback.message.edit_text(
        text,
        reply_markup=reply_markup,
    )


def _parse_int(value: str) -> int:
    try:
        return int(value.strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Ожидалось целое число."
        ) from exc


def _parse_decimal(value: str) -> Decimal:
    try:
        result = Decimal(
            value.strip().replace(",", ".")
        )
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(
            "Ожидалось число."
        ) from exc

    if not result.is_finite():
        raise ValueError(
            "Число должно быть конечным."
        )

    return result


def _split_pipe(
    text: str,
    expected: int,
) -> list[str]:
    parts = [
        part.strip()
        for part in text.split("|")
    ]

    if len(parts) != expected:
        raise ValueError(
            f"Нужно указать {expected} значения через |."
        )

    return parts


def _format_settings(
    values: dict,
) -> str:
    if not values:
        return "Настройки отсутствуют."

    lines = []

    for key in sorted(values):
        lines.append(
            f"<code>{key}</code> = "
            f"<code>{values[key]}</code>"
        )

    return "\n".join(lines)


# ============================================================================
# MAIN
# ============================================================================


@router.callback_query(F.data == "founder:main")
async def founder_main(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.clear()

    await _edit(
        callback,
        "👑 <b>Founder Panel</b>\n\n"
        "Выбери нужный раздел:",
        founder_main_keyboard(),
    )


@router.callback_query(F.data == "founder:close")
async def founder_close(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.clear()

    await callback.answer()

    if callback.message is not None:
        await callback.message.delete()


# ============================================================================
# CHATS
# ============================================================================


@router.callback_query(F.data == "founder:chats")
async def founder_chats(
    callback: CallbackQuery,
) -> None:
    await _edit(
        callback,
        "💬 <b>Управление чатами</b>\n\n"
        "Добавляй Telegram-чаты и выбирай чат, "
        "для которого будут изменяться настройки.",
        founder_chats_keyboard(),
    )


@router.callback_query(F.data == "founder:chats:add")
async def founder_chats_add(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()

    await state.set_state(
        FounderStates.target_chat
    )

    if callback.message is not None:
        await callback.message.edit_text(
            "➕ <b>Добавление / выбор чата</b>\n\n"
            "Отправь Telegram chat ID.\n\n"
            "Пример:\n"
            "<code>-1001234567890</code>\n\n"
            "После этого чат станет текущим для "
            "Founder Panel.",
        )


@router.message(
    StateFilter(FounderStates.target_chat)
)
async def founder_target_chat_message(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    try:
        chat_id = _parse_int(
            message.text or ""
        )

        if chat_id == 0:
            raise ValueError(
                "chat_id не может быть 0."
            )

        _, _, settings_repo, _, _ = _repositories(
            session
        )

        chat = await settings_repo.get_or_create_chat(
            chat_id=chat_id,
            chat_type="group",
        )

        await state.update_data(
            target_chat_id=chat.id,
        )

        await state.clear()

        await message.answer(
            "✅ <b>Чат выбран</b>\n\n"
            f"Chat ID: <code>{chat.id}</code>\n\n"
            "Теперь Founder Panel будет работать "
            "с настройками этого чата.",
            reply_markup=founder_chat_settings_keyboard(
                chat.id
            ),
        )

    except ValueError as exc:
        await message.answer(
            f"❌ {exc}\n\n"
            "Отправь корректный Telegram chat ID."
        )


@router.callback_query(
    F.data == "founder:chats:list"
)
async def founder_chats_list(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    result = await session.execute(
        select(Chat)
        .order_by(Chat.id)
        .limit(50)
    )

    chats = result.scalars().all()

    if not chats:
        await _edit(
            callback,
            "📋 <b>Подключённые чаты</b>\n\n"
            "Пока ни одного чата нет.",
            founder_chats_keyboard(),
        )
        return

    lines = [
        "📋 <b>Подключённые чаты</b>",
        "",
    ]

    for chat in chats:
        title = chat.title or "Без названия"

        lines.append(
            f"• <b>{title}</b>\n"
            f"  ID: <code>{chat.id}</code>"
        )

    await _edit(
        callback,
        "\n".join(lines),
        founder_chats_keyboard(),
    )


@router.callback_query(
    F.data == "founder:chats:settings"
)
async def founder_chats_settings(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    chat_id = await _target_chat(state)

    if chat_id is None:
        await _edit(
            callback,
            "⚙️ <b>Настройки чата</b>\n\n"
            "Сначала выбери чат.",
            founder_chats_keyboard(),
        )
        return

    await _edit(
        callback,
        "⚙️ <b>Настройки чата</b>\n\n"
        f"Текущий chat ID:\n"
        f"<code>{chat_id}</code>\n\n"
        "Выбери нужный раздел.",
        founder_chat_settings_keyboard(
            chat_id
        ),
    )


@router.callback_query(
    F.data.startswith("founder:chat:")
)
async def founder_chat_section(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    parts = (
        callback.data or ""
    ).split(":")

    if len(parts) != 4:
        return

    section = parts[2]

    try:
        chat_id = int(parts[3])
    except ValueError:
        await callback.answer(
            "Некорректный chat ID.",
            show_alert=True,
        )
        return

    _, _, settings_repo, _, _ = _repositories(
        session
    )

    values = await settings_repo.get_all(
        chat_id=chat_id
    )

    prefix_map = {
        "economy": "rewards.",
        "moderation": "moderation.",
        "games": "games.",
        "interactions": "interactions.",
        "characters": "character.",
        "rewards": "rewards.",
        "welcome": "welcome.",
        "logging": "logging.",
        "localization": "localization.",
    }

    prefix = prefix_map.get(
        section,
        "",
    )

    filtered = {
        key: value
        for key, value in values.items()
        if key.startswith(prefix)
    }

    await state.update_data(
        target_chat_id=chat_id,
        setting_prefix=prefix,
    )

    await _edit(
        callback,
        f"⚙️ <b>Настройки: {section}</b>\n\n"
        f"Chat ID: <code>{chat_id}</code>\n\n"
        f"{_format_settings(filtered)}\n\n"
        "Для изменения значения используй кнопку "
        "«Изменить значение».",
        founder_economy_settings_keyboard(),
    )


# ============================================================================
# ECONOMY
# ============================================================================


@router.callback_query(
    F.data == "founder:economy"
)
async def founder_economy(
    callback: CallbackQuery,
) -> None:
    await _edit(
        callback,
        "💰 <b>Экономика</b>\n\n"
        "Настройки сохраняются отдельно для выбранного "
        "Telegram-чата.",
        founder_economy_keyboard(),
    )


@router.callback_query(
    F.data.startswith("founder:economy:")
)
async def founder_economy_section(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    data = callback.data or ""

    section = data.removeprefix(
        "founder:economy:"
    )

    if section in {
        "view",
        "edit",
        "reset",
    }:
        return

    chat_id = await _require_target_chat(
        callback,
        state,
    )

    if chat_id is None:
        return

    prefix_map = {
        "currency": "currency.",
        "messages": "rewards.message.",
        "rewards": "rewards.hourly.",
        "bank": "bank.",
        "passive": "passive.",
        "games": "games.",
        "interactions": "interactions.",
        "credits": "credits.",
        "levels": "levels.",
        "transactions": "",
    }

    prefix = prefix_map.get(
        section,
        "",
    )

    await state.update_data(
        target_chat_id=chat_id,
        setting_prefix=prefix,
        setting_section=section,
    )

    if section == "transactions":
        result = await session.execute(
            select(Transaction)
            .where(
                Transaction.user_id.is_not(None)
            )
            .order_by(
                Transaction.id.desc()
            )
            .limit(20)
        )

        transactions = result.scalars().all()

        if not transactions:
            text = (
                "📜 <b>История операций</b>\n\n"
                "Транзакций пока нет."
            )
        else:
            lines = [
                "📜 <b>Последние операции</b>",
                "",
            ]

            for tx in transactions:
                lines.append(
                    f"#{tx.id} | "
                    f"user=<code>{tx.user_id}</code> | "
                    f"{tx.amount} | "
                    f"{tx.source}"
                )

            text = "\n".join(lines)

        await _edit(
            callback,
            text,
            founder_economy_keyboard(),
        )
        return

    values = await session.get(
        Chat,
        chat_id,
    )

    if values is None:
        await _edit(
            callback,
            "❌ Чат не найден.\n\n"
            "Сначала добавь его через раздел «Чаты».",
            founder_chats_keyboard(),
        )
        return

    settings_repo = SettingsRepository(
        session
    )

    current = await settings_repo.get_by_prefix(
        chat_id=chat_id,
        prefix=prefix,
    )

    await _edit(
        callback,
        f"⚙️ <b>{section}</b>\n\n"
        f"Chat ID: <code>{chat_id}</code>\n\n"
        f"{_format_settings(current)}",
        founder_economy_settings_keyboard(),
    )


@router.callback_query(
    F.data == "founder:economy:view"
)
async def founder_economy_view(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    chat_id = await _require_target_chat(
        callback,
        state,
    )

    if chat_id is None:
        return

    data = await state.get_data()

    prefix = data.get(
        "setting_prefix",
        "",
    )

    settings_repo = SettingsRepository(
        session
    )

    values = await settings_repo.get_by_prefix(
        chat_id=chat_id,
        prefix=prefix,
    )

    await _edit(
        callback,
        "📋 <b>Текущие настройки</b>\n\n"
        f"Chat ID: <code>{chat_id}</code>\n\n"
        f"{_format_settings(values)}",
        founder_economy_settings_keyboard(),
    )


@router.callback_query(
    F.data == "founder:economy:edit"
)
async def founder_economy_edit(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    chat_id = await _require_target_chat(
        callback,
        state,
    )

    if chat_id is None:
        return

    data = await state.get_data()

    prefix = data.get(
        "setting_prefix",
        "",
    )

    await callback.answer()

    await state.set_state(
        FounderStates.setting
    )

    if callback.message is not None:
        await callback.message.edit_text(
            "✏️ <b>Изменение настройки</b>\n\n"
            f"Chat ID: <code>{chat_id}</code>\n"
            f"Prefix: <code>{prefix or '*'}</code>\n\n"
            "Отправь:\n"
            "<code>ключ = значение</code>\n\n"
            "Например:\n"
            "<code>rewards.hourly.currency = 50</code>\n\n"
            "Если ключ не начинается с текущего prefix, "
            "он будет использован как указан.",
        )


@router.message(
    StateFilter(FounderStates.setting)
)
async def founder_setting_message(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    text = (message.text or "").strip()

    if "=" not in text:
        await message.answer(
            "❌ Формат:\n"
            "<code>ключ = значение</code>"
        )
        return

    key, value = text.split(
        "=",
        1,
    )

    key = key.strip()
    value = value.strip()

    if not key:
        await message.answer(
            "❌ Ключ не может быть пустым."
        )
        return

    data = await state.get_data()

    chat_id = data.get(
        "target_chat_id"
    )

    if chat_id is None:
        await state.clear()
        await message.answer(
            "❌ Чат не выбран."
        )
        return

    try:
        if value.lower() in {
            "true",
            "false",
        }:
            parsed_value = (
                value.lower() == "true"
            )
        else:
            try:
                parsed_value = _parse_int(value)
            except ValueError:
                try:
                    parsed_value = _parse_decimal(
                        value
                    )
                except ValueError:
                    parsed_value = value

        settings_repo = SettingsRepository(
            session
        )

        await settings_repo.set(
            chat_id=int(chat_id),
            key=key,
            value=parsed_value,
        )

        await state.set_state(
            FounderStates.setting
        )

        await message.answer(
            "✅ <b>Настройка сохранена</b>\n\n"
            f"<code>{key}</code> = "
            f"<code>{parsed_value}</code>\n\n"
            "Можешь отправить ещё одно "
            "значение или открыть панель.",
        )

    except Exception as exc:
        await message.answer(
            f"❌ Не удалось сохранить настройку:\n"
            f"<code>{exc}</code>"
        )


@router.callback_query(
    F.data == "founder:economy:reset"
)
async def founder_economy_reset(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    chat_id = await _require_target_chat(
        callback,
        state,
    )

    if chat_id is None:
        return

    data = await state.get_data()

    prefix = data.get(
        "setting_prefix",
        "",
    )

    if not prefix:
        await _edit(
            callback,
            "⚠️ Для полного сброса настроек "
            "нужно выбрать конкретный раздел.",
            founder_economy_keyboard(),
        )
        return

    settings_repo = SettingsRepository(
        session
    )

    count = await settings_repo.delete_by_prefix(
        chat_id=chat_id,
        prefix=prefix,
    )

    await _edit(
        callback,
        "🔄 <b>Настройки сброшены</b>\n\n"
        f"Удалено значений: <b>{count}</b>",
        founder_economy_keyboard(),
    )


# ============================================================================
# USERS
# ============================================================================


@router.callback_query(
    F.data == "founder:users"
)
async def founder_users(
    callback: CallbackQuery,
) -> None:
    await _edit(
        callback,
        "👥 <b>Пользователи</b>\n\n"
        "Управление пользователями.",
        founder_users_keyboard(),
    )


@router.callback_query(
    F.data.in_({
        "founder:users:search",
        "founder:users:id",
    })
)
async def founder_user_lookup_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()

    await state.set_state(
        FounderStates.user_lookup
    )

    if callback.message is not None:
        await callback.message.edit_text(
            "🔎 <b>Поиск пользователя</b>\n\n"
            "Отправь Telegram ID или username.\n\n"
            "Пример:\n"
            "<code>123456789</code>\n"
            "<code>@username</code>",
        )


@router.message(
    StateFilter(FounderStates.user_lookup)
)
async def founder_user_lookup(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    value = (message.text or "").strip()

    user: User | None = None

    users_repo = UserRepository(
        session
    )

    try:
        user_id = _parse_int(
            value.lstrip("@")
        )

        user = await users_repo.get_by_id(
            user_id
        )

    except ValueError:
        username = value.lstrip("@")

        result = await session.execute(
            select(User).where(
                User.username.ilike(username)
            )
        )

        user = result.scalar_one_or_none()

    if user is None:
        await message.answer(
            "❌ Пользователь не найден."
        )
        return

    await state.clear()

    await message.answer(
        "👤 <b>Пользователь найден</b>\n\n"
        f"ID: <code>{user.id}</code>\n"
        f"Username: "
        f"<code>{user.username or '-'}</code>\n"
        f"Имя: {user.first_name}\n"
        f"XP: <b>{user.xp}</b>\n"
        f"Уровень: <b>{user.level}</b>\n"
        f"Репутация: <b>{user.reputation}</b>\n"
        f"Активен: <b>{user.is_active}</b>",
        reply_markup=founder_user_actions_keyboard(
            user.id
        ),
    )


@router.callback_query(
    F.data.startswith("founder:user:view:")
)
async def founder_user_view(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    user_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    user = await UserRepository(
        session
    ).get_by_id(user_id)

    if user is None:
        await callback.answer(
            "Пользователь не найден.",
            show_alert=True,
        )
        return

    await _edit(
        callback,
        "👤 <b>Профиль пользователя</b>\n\n"
        f"ID: <code>{user.id}</code>\n"
        f"Username: "
        f"<code>{user.username or '-'}</code>\n"
        f"Имя: {user.first_name}\n"
        f"Фамилия: {user.last_name or '-'}\n\n"
        f"💰 XP: <b>{user.xp}</b>\n"
        f"📈 Уровень: <b>{user.level}</b>\n"
        f"⭐ Репутация: <b>{user.reputation}</b>\n"
        f"💬 Сообщений: <b>{user.message_count}</b>\n"
        f"Статус: <b>{'активен' if user.is_active else 'отключён'}</b>",
        founder_user_actions_keyboard(
            user.id
        ),
    )


@router.callback_query(
    F.data.startswith("founder:user:balance:")
)
async def founder_user_balance_view(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    user_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    balance = await EconomyRepository(
        session
    ).get_balance(user_id)

    await _edit(
        callback,
        "💰 <b>Баланс</b>\n\n"
        f"User ID: <code>{user_id}</code>\n"
        f"Баланс: <b>{balance}</b>",
        founder_user_actions_keyboard(
            user_id
        ),
    )


@router.callback_query(
    F.data == "founder:users:balance"
)
async def founder_user_balance_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()

    await state.set_state(
        FounderStates.user_balance
    )

    if callback.message is not None:
        await callback.message.edit_text(
            "💰 <b>Изменение баланса</b>\n\n"
            "Отправь:\n"
            "<code>user_id amount</code>\n\n"
            "Пример:\n"
            "<code>123456789 5000</code>\n\n"
            "Значение устанавливается напрямую.",
        )


@router.message(
    StateFilter(FounderStates.user_balance)
)
async def founder_user_balance_message(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    parts = (message.text or "").split()

    if len(parts) != 2:
        await message.answer(
            "❌ Формат: <code>user_id amount</code>"
        )
        return

    try:
        user_id = _parse_int(parts[0])
        amount = _parse_decimal(parts[1])

        if amount < 0:
            raise ValueError(
                "Баланс не может быть отрицательным."
            )

        user = await UserRepository(
            session
        ).get_by_id(user_id)

        if user is None:
            raise ValueError(
                "Пользователь не найден."
            )

        await EconomyRepository(
            session
        ).set_balance(
            user_id,
            amount,
        )

        await state.clear()

        await message.answer(
            "✅ Баланс установлен.\n\n"
            f"User ID: <code>{user_id}</code>\n"
            f"Новый баланс: <b>{amount}</b>",
            reply_markup=founder_users_keyboard(),
        )

    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )


@router.callback_query(
    F.data.startswith("founder:user:xp:")
)
async def founder_user_xp_view(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    user_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    user = await UserRepository(
        session
    ).get_by_id(user_id)

    if user is None:
        await callback.answer(
            "Пользователь не найден.",
            show_alert=True,
        )
        return

    await _edit(
        callback,
        "⭐ <b>XP</b>\n\n"
        f"User ID: <code>{user_id}</code>\n"
        f"XP: <b>{user.xp}</b>\n"
        f"Уровень: <b>{user.level}</b>",
        founder_user_actions_keyboard(
            user_id
        ),
    )


@router.callback_query(
    F.data == "founder:users:xp"
)
async def founder_user_xp_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()

    await state.set_state(
        FounderStates.user_xp
    )

    if callback.message is not None:
        await callback.message.edit_text(
            "⭐ <b>Изменение XP</b>\n\n"
            "Отправь:\n"
            "<code>user_id xp</code>",
        )


@router.message(
    StateFilter(FounderStates.user_xp)
)
async def founder_user_xp_message(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    parts = (message.text or "").split()

    if len(parts) != 2:
        await message.answer(
            "❌ Формат: <code>user_id xp</code>"
        )
        return

    try:
        user_id = _parse_int(parts[0])
        xp = _parse_int(parts[1])

        result = await UserRepository(
            session
        ).set_xp(
            user_id,
            xp,
        )

        if result is None:
            raise ValueError(
                "Пользователь не найден."
            )

        await state.clear()

        await message.answer(
            "✅ XP изменён.\n\n"
            f"User ID: <code>{user_id}</code>\n"
            f"XP: <b>{result.xp}</b>",
            reply_markup=founder_users_keyboard(),
        )

    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )


@router.callback_query(
    F.data.startswith("founder:user:disable:")
)
async def founder_user_disable(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    user_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    success = await UserRepository(
        session
    ).set_active(
        user_id,
        False,
    )

    await _edit(
        callback,
        (
            "✅ Пользователь отключён."
            if success
            else "❌ Пользователь не найден."
        ),
        founder_users_keyboard(),
    )


# ============================================================================
# RACES
# ============================================================================


@router.callback_query(
    F.data == "founder:races"
)
async def founder_races(
    callback: CallbackQuery,
) -> None:
    await _edit(
        callback,
        "🧬 <b>Расы</b>\n\n"
        "Управление расами персонажей.",
        founder_races_keyboard(),
    )


@router.callback_query(
    F.data == "founder:races:list:1"
)
async def founder_races_list(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    repo = CharacterRepository(
        session
    )

    races = await repo.get_active_races()

    if not races:
        text = (
            "📋 <b>Расы</b>\n\n"
            "Активных рас нет."
        )
    else:
        lines = [
            "📋 <b>Расы</b>",
            "",
        ]

        for race in races:
            lines.append(
                f"🧬 <b>{race.name}</b> "
                f"(ID <code>{race.id}</code>)\n"
                f"HP: {race.base_hp} | "
                f"STR: {race.base_strength} | "
                f"DEF: {race.base_defense}\n"
                f"LUCK: {race.base_luck} | "
                f"SPD: {race.base_speed} | "
                f"INT: {race.base_intelligence}"
            )

        text = "\n\n".join(lines)

    await _edit(
        callback,
        text,
        founder_races_keyboard(),
    )


@router.callback_query(
    F.data == "founder:races:create"
)
async def founder_races_create(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()

    await state.set_state(
        FounderStates.create_race
    )

    if callback.message is not None:
        await callback.message.edit_text(
            "➕ <b>Создание расы</b>\n\n"
            "Отправь 8 значений через <code>|</code>:\n\n"
            "<code>Название | Описание | HP | STR | DEF | LUCK | SPD | INT</code>\n\n"
            "Пример:\n"
            "<code>Орк | Сильная раса | 130 | 15 | 12 | 5 | 8 | 6</code>",
        )


@router.message(
    StateFilter(FounderStates.create_race)
)
async def founder_create_race_message(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    try:
        parts = _split_pipe(
            message.text or "",
            8,
        )

        race = await CharacterRepository(
            session
        ).create_race(
            name=parts[0],
            description=parts[1],
            base_hp=_parse_int(parts[2]),
            base_strength=_parse_int(parts[3]),
            base_defense=_parse_int(parts[4]),
            base_luck=_parse_int(parts[5]),
            base_speed=_parse_int(parts[6]),
            base_intelligence=_parse_int(parts[7]),
        )

        await state.clear()

        await message.answer(
            "✅ <b>Раса создана</b>\n\n"
            f"ID: <code>{race.id}</code>\n"
            f"Название: <b>{race.name}</b>",
            reply_markup=founder_races_keyboard(),
        )

    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )


@router.callback_query(
    F.data.startswith("founder:race:view:")
)
async def founder_race_view(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    race_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    race = await CharacterRepository(
        session
    ).get_race(race_id)

    if race is None:
        await callback.answer(
            "Раса не найдена.",
            show_alert=True,
        )
        return

    await _edit(
        callback,
        f"🧬 <b>{race.name}</b>\n\n"
        f"ID: <code>{race.id}</code>\n"
        f"{race.description or '-'}\n\n"
        f"HP: {race.base_hp}\n"
        f"STR: {race.base_strength}\n"
        f"DEF: {race.base_defense}\n"
        f"LUCK: {race.base_luck}\n"
        f"SPD: {race.base_speed}\n"
        f"INT: {race.base_intelligence}\n"
        f"Активна: {race.is_active}",
        founder_race_actions_keyboard(
            race.id
        ),
    )


@router.callback_query(
    F.data.startswith("founder:race:delete:")
)
async def founder_race_delete(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    race_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    race = await CharacterRepository(
        session
    ).update_race(
        race_id,
        is_active=False,
    )

    await _edit(
        callback,
        (
            "✅ Раса отключена."
            if race is not None
            else "❌ Раса не найдена."
        ),
        founder_races_keyboard(),
    )


# ============================================================================
# RANKS
# ============================================================================


@router.callback_query(
    F.data == "founder:ranks"
)
async def founder_ranks(
    callback: CallbackQuery,
) -> None:
    await _edit(
        callback,
        "🏅 <b>Ранги</b>\n\n"
        "Управление рангами.",
        founder_ranks_keyboard(),
    )


@router.callback_query(
    F.data == "founder:ranks:list:1"
)
async def founder_ranks_list(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    ranks = await CharacterRepository(
        session
    ).get_active_ranks()

    if not ranks:
        text = (
            "📋 <b>Ранги</b>\n\n"
            "Активных рангов нет."
        )
    else:
        lines = [
            "📋 <b>Ранги</b>",
            "",
        ]

        for rank in ranks:
            lines.append(
                f"🏅 <b>{rank.name}</b> "
                f"(ID <code>{rank.id}</code>)\n"
                f"Level: {rank.level}\n"
                f"Требования: "
                f"LVL {rank.required_level}, "
                f"XP {rank.required_xp}, "
                f"REP {rank.required_reputation}"
            )

        text = "\n\n".join(lines)

    await _edit(
        callback,
        text,
        founder_ranks_keyboard(),
    )


@router.callback_query(
    F.data == "founder:ranks:create"
)
async def founder_ranks_create(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()

    await state.set_state(
        FounderStates.create_rank
    )

    if callback.message is not None:
        await callback.message.edit_text(
            "➕ <b>Создание ранга</b>\n\n"
            "Отправь 6 значений через <code>|</code>:\n\n"
            "<code>Название | Level | Описание | Required Level | Required XP | Required Reputation</code>",
        )


@router.message(
    StateFilter(FounderStates.create_rank)
)
async def founder_create_rank_message(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    try:
        parts = _split_pipe(
            message.text or "",
            6,
        )

        rank = await CharacterRepository(
            session
        ).create_rank(
            name=parts[0],
            level=_parse_int(parts[1]),
            description=parts[2],
            required_level=_parse_int(parts[3]),
            required_xp=_parse_int(parts[4]),
            required_reputation=_parse_int(parts[5]),
        )

        await state.clear()

        await message.answer(
            "✅ <b>Ранг создан</b>\n\n"
            f"ID: <code>{rank.id}</code>\n"
            f"Название: <b>{rank.name}</b>\n"
            f"Level: <b>{rank.level}</b>",
            reply_markup=founder_ranks_keyboard(),
        )

    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )


@router.callback_query(
    F.data.startswith("founder:rank:view:")
)
async def founder_rank_view(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    rank_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    rank = await CharacterRepository(
        session
    ).get_rank(rank_id)

    if rank is None:
        await callback.answer(
            "Ранг не найден.",
            show_alert=True,
        )
        return

    await _edit(
        callback,
        f"🏅 <b>{rank.name}</b>\n\n"
        f"ID: <code>{rank.id}</code>\n"
        f"Level: {rank.level}\n"
        f"{rank.description or '-'}\n\n"
        f"Требования:\n"
        f"LVL: {rank.required_level}\n"
        f"XP: {rank.required_xp}\n"
        f"REP: {rank.required_reputation}\n\n"
        f"Бонусы:\n"
        f"HP: {rank.hp_bonus}\n"
        f"STR: {rank.strength_bonus}\n"
        f"DEF: {rank.defense_bonus}\n"
        f"LUCK: {rank.luck_bonus}\n"
        f"SPD: {rank.speed_bonus}\n"
        f"INT: {rank.intelligence_bonus}",
        founder_rank_actions_keyboard(
            rank.id
        ),
    )


@router.callback_query(
    F.data.startswith("founder:rank:delete:")
)
async def founder_rank_delete(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    rank_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    rank = await CharacterRepository(
        session
    ).update_rank(
        rank_id,
        is_active=False,
    )

    await _edit(
        callback,
        (
            "✅ Ранг отключён."
            if rank is not None
            else "❌ Ранг не найден."
        ),
        founder_ranks_keyboard(),
    )


# ============================================================================
# ABILITIES
# ============================================================================


@router.callback_query(
    F.data == "founder:abilities"
)
async def founder_abilities(
    callback: CallbackQuery,
) -> None:
    await _edit(
        callback,
        "✨ <b>Способности</b>\n\n"
        "Управление способностями.",
        founder_abilities_keyboard(),
    )


@router.callback_query(
    F.data == "founder:abilities:list:1"
)
async def founder_abilities_list(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    abilities = await CharacterRepository(
        session
    ).get_active_abilities()

    if not abilities:
        text = (
            "📋 <b>Способности</b>\n\n"
            "Активных способностей нет."
        )
    else:
        lines = [
            "📋 <b>Способности</b>",
            "",
        ]

        for ability in abilities:
            lines.append(
                f"✨ <b>{ability.name}</b> "
                f"(ID <code>{ability.id}</code>)\n"
                f"Тип: {ability.ability_type}\n"
                f"Effect: {ability.effect_value}\n"
                f"Cooldown: {ability.cooldown_seconds}s"
            )

        text = "\n\n".join(lines)

    await _edit(
        callback,
        text,
        founder_abilities_keyboard(),
    )


@router.callback_query(
    F.data == "founder:abilities:create"
)
async def founder_abilities_create(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()

    await state.set_state(
        FounderStates.create_ability
    )

    if callback.message is not None:
        await callback.message.edit_text(
            "➕ <b>Создание способности</b>\n\n"
            "Отправь 6 значений через <code>|</code>:\n\n"
            "<code>Название | Описание | Тип | Значение | Duration | Cooldown</code>",
        )


@router.message(
    StateFilter(FounderStates.create_ability)
)
async def founder_create_ability_message(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    try:
        parts = _split_pipe(
            message.text or "",
            6,
        )

        ability = await CharacterRepository(
            session
        ).create_ability(
            name=parts[0],
            description=parts[1],
            ability_type=parts[2],
            effect_value=_parse_int(parts[3]),
            duration_seconds=_parse_int(parts[4]),
            cooldown_seconds=_parse_int(parts[5]),
        )

        await state.clear()

        await message.answer(
            "✅ <b>Способность создана</b>\n\n"
            f"ID: <code>{ability.id}</code>\n"
            f"Название: <b>{ability.name}</b>",
            reply_markup=founder_abilities_keyboard(),
        )

    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )


@router.callback_query(
    F.data.startswith("founder:ability:view:")
)
async def founder_ability_view(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    ability_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    ability = await CharacterRepository(
        session
    ).get_ability(ability_id)

    if ability is None:
        await callback.answer(
            "Способность не найдена.",
            show_alert=True,
        )
        return

    await _edit(
        callback,
        f"✨ <b>{ability.name}</b>\n\n"
        f"ID: <code>{ability.id}</code>\n"
        f"Тип: {ability.ability_type}\n"
        f"Описание: {ability.description or '-'}\n\n"
        f"Значение: {ability.effect_value}\n"
        f"Duration: {ability.duration_seconds}s\n"
        f"Cooldown: {ability.cooldown_seconds}s\n"
        f"Активна: {ability.is_active}",
        founder_ability_actions_keyboard(
            ability.id
        ),
    )


@router.callback_query(
    F.data.startswith("founder:ability:delete:")
)
async def founder_ability_delete(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    ability_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    ability = await CharacterRepository(
        session
    ).update_ability(
        ability_id,
        is_active=False,
    )

    await _edit(
        callback,
        (
            "✅ Способность отключена."
            if ability is not None
            else "❌ Способность не найдена."
        ),
        founder_abilities_keyboard(),
    )


# ============================================================================
# SHOP
# ============================================================================


@router.callback_query(
    F.data == "founder:shop"
)
async def founder_shop(
    callback: CallbackQuery,
) -> None:
    await _edit(
        callback,
        "🛍 <b>Магазин</b>\n\n"
        "Управление предметами.",
        founder_shop_keyboard(),
    )


@router.callback_query(
    F.data == "founder:shop:list:1"
)
async def founder_shop_list(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    items = await InventoryRepository(
        session
    ).get_active_items()

    if not items:
        text = (
            "📋 <b>Товары</b>\n\n"
            "Активных товаров нет."
        )
    else:
        lines = [
            "📋 <b>Товары</b>",
            "",
        ]

        for item in items:
            lines.append(
                f"🛍 <b>{item.name}</b> "
                f"(ID <code>{item.id}</code>)\n"
                f"Цена: {item.price}\n"
                f"Тип: {item.item_type}\n"
                f"Редкость: {item.rarity}"
            )

        text = "\n\n".join(lines)

    await _edit(
        callback,
        text,
        founder_shop_keyboard(),
    )


@router.callback_query(
    F.data == "founder:shop:create"
)
async def founder_shop_create(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()

    await state.set_state(
        FounderStates.create_item
    )

    if callback.message is not None:
        await callback.message.edit_text(
            "➕ <b>Создание товара</b>\n\n"
            "Отправь 5 значений через <code>|</code>:\n\n"
            "<code>Название | Описание | Тип | Редкость | Цена</code>",
        )


@router.message(
    StateFilter(FounderStates.create_item)
)
async def founder_create_item_message(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    try:
        parts = _split_pipe(
            message.text or "",
            5,
        )

        item = await InventoryRepository(
            session
        ).create_item(
            name=parts[0],
            description=parts[1],
            item_type=parts[2],
            rarity=parts[3],
            price=_parse_decimal(parts[4]),
        )

        await state.clear()

        await message.answer(
            "✅ <b>Товар создан</b>\n\n"
            f"ID: <code>{item.id}</code>\n"
            f"Название: <b>{item.name}</b>\n"
            f"Цена: <b>{item.price}</b>",
            reply_markup=founder_shop_keyboard(),
        )

    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )


@router.callback_query(
    F.data.startswith("founder:item:view:")
)
async def founder_item_view(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    item_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    item = await InventoryRepository(
        session
    ).get_item(item_id)

    if item is None:
        await callback.answer(
            "Товар не найден.",
            show_alert=True,
        )
        return

    await _edit(
        callback,
        f"🛍 <b>{item.name}</b>\n\n"
        f"ID: <code>{item.id}</code>\n"
        f"{item.description or '-'}\n\n"
        f"Тип: {item.item_type}\n"
        f"Редкость: {item.rarity}\n"
        f"Цена: {item.price}\n"
        f"Активен: {item.is_active}",
        founder_item_actions_keyboard(
            item.id
        ),
    )


@router.callback_query(
    F.data.startswith("founder:item:delete:")
)
async def founder_item_delete(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    item_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    item = await InventoryRepository(
        session
    ).update_item(
        item_id,
        is_active=False,
    )

    await _edit(
        callback,
        (
            "✅ Товар отключён."
            if item is not None
            else "❌ Товар не найден."
        ),
        founder_shop_keyboard(),
    )


# ============================================================================
# CASES
# ============================================================================


@router.callback_query(
    F.data == "founder:cases"
)
async def founder_cases(
    callback: CallbackQuery,
) -> None:
    await _edit(
        callback,
        "🎁 <b>Кейсы</b>\n\n"
        "Управление кейсами.",
        founder_cases_keyboard(),
    )


@router.callback_query(
    F.data == "founder:cases:list:1"
)
async def founder_cases_list(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    result = await session.execute(
        select(Case)
        .where(
            Case.is_active.is_(True)
        )
        .order_by(Case.id)
    )

    cases = result.scalars().all()

    if not cases:
        text = (
            "📋 <b>Кейсы</b>\n\n"
            "Активных кейсов нет."
        )
    else:
        lines = [
            "📋 <b>Кейсы</b>",
            "",
        ]

        for case in cases:
            lines.append(
                f"🎁 <b>{case.name}</b> "
                f"(ID <code>{case.id}</code>)\n"
                f"Цена: {case.price} "
                f"{case.currency_type}"
            )

        text = "\n\n".join(lines)

    await _edit(
        callback,
        text,
        founder_cases_keyboard(),
    )


@router.callback_query(
    F.data == "founder:cases:create"
)
async def founder_cases_create(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()

    await state.set_state(
        FounderStates.create_case
    )

    if callback.message is not None:
        await callback.message.edit_text(
            "➕ <b>Создание кейса</b>\n\n"
            "Отправь 4 значения через <code>|</code>:\n\n"
            "<code>Название | Описание | Цена | currency/gems</code>",
        )


@router.message(
    StateFilter(FounderStates.create_case)
)
async def founder_create_case_message(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    try:
        parts = _split_pipe(
            message.text or "",
            4,
        )

        case = Case(
            name=parts[0],
            description=parts[1],
            price=_parse_decimal(parts[2]),
            currency_type=parts[3],
        )

        session.add(case)

        await session.flush()

        await state.clear()

        await message.answer(
            "✅ <b>Кейс создан</b>\n\n"
            f"ID: <code>{case.id}</code>\n"
            f"Название: <b>{case.name}</b>",
            reply_markup=founder_cases_keyboard(),
        )

    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )


# ============================================================================
# MODERATION
# ============================================================================


@router.callback_query(
    F.data == "founder:moderation"
)
async def founder_moderation(
    callback: CallbackQuery,
) -> None:
    await _edit(
        callback,
        "🛡 <b>Модерация</b>\n\n"
        "Настройки модерации выбранного чата.",
        founder_moderation_keyboard(),
    )


@router.callback_query(
    F.data.startswith("founder:moderation:")
)
async def founder_moderation_section(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    section = (
        (callback.data or "")
        .removeprefix(
            "founder:moderation:"
        )
    )

    if section in {
        "settings",
        "filters",
        "warnings",
        "mutes",
        "bans",
        "levels",
        "history",
    }:
        chat_id = await _require_target_chat(
            callback,
            state,
        )

        if chat_id is None:
            return

        settings_repo = SettingsRepository(
            session
        )

        values = await settings_repo.get_by_prefix(
            chat_id=chat_id,
            prefix="moderation.",
        )

        await _edit(
            callback,
            f"🛡 <b>Модерация: {section}</b>\n\n"
            f"{_format_settings(values)}",
            founder_moderation_keyboard(),
        )


# ============================================================================
# SYSTEM
# ============================================================================


@router.callback_query(
    F.data == "founder:system"
)
async def founder_system(
    callback: CallbackQuery,
) -> None:
    await _edit(
        callback,
        "⚙️ <b>Система</b>\n\n"
        "Системное управление Founder Panel.",
        founder_system_keyboard(),
    )


@router.callback_query(
    F.data.startswith("founder:system:")
)
async def founder_system_section(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    section = (
        (callback.data or "")
        .removeprefix(
            "founder:system:"
        )
    )

    if section == "founder":
        await _edit(
            callback,
            "👑 <b>Основатель</b>\n\n"
            "Founder ID: "
            f"<code>{callback.from_user.id}</code>",
            founder_system_keyboard(),
        )
        return

    if section == "permissions":
        result = await session.execute(
            select(Permission)
            .where(
                Permission.is_active.is_(True)
            )
            .order_by(Permission.id)
        )

        permissions = result.scalars().all()

        if not permissions:
            text = (
                "🔐 <b>Права</b>\n\n"
                "Права ещё не созданы."
            )
        else:
            text = (
                "🔐 <b>Права</b>\n\n"
                + "\n".join(
                    f"• <code>{p.key}</code> — {p.name}"
                    for p in permissions
                )
            )

        await _edit(
            callback,
            text,
            founder_system_keyboard(),
        )
        return

    if section == "settings":
        await _edit(
            callback,
            "⚙️ <b>Глобальные настройки</b>\n\n"
            "Глобальные настройки находятся в "
            "конфигурации приложения.\n\n"
            "Чат-зависимые настройки изменяются "
            "через раздел «Чаты» → настройки.",
            founder_system_keyboard(),
        )
        return

    if section == "info":
        text = (
            "🔄 <b>Системная информация</b>\n\n"
            f"Founder ID: "
            f"<code>{callback.from_user.id}</code>\n"
            "Database: SQLAlchemy\n"
            "Panel: enabled"
        )

        await _edit(
            callback,
            text,
            founder_system_keyboard(),
        )
        return

    if section == "cleanup":
        await _edit(
            callback,
            "🧹 <b>Очистка данных</b>\n\n"
            "Автоматическое удаление данных здесь "
            "не выполняется во избежание случайной потери.",
            founder_system_keyboard(),
        )


# ============================================================================
# STATISTICS
# ============================================================================


@router.callback_query(
    F.data == "founder:statistics"
)
async def founder_statistics(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    async def count(model):
        result = await session.execute(
            select(func.count())
            .select_from(model)
        )

        return int(
            result.scalar_one()
        )

    users = await count(User)
    wallets = await count(Wallet)
    transactions = await count(Transaction)
    characters = await count(Character)
    races = await count(Race)
    ranks = await count(CharacterRank)
    abilities = await count(Ability)
    items = await count(Item)
    cases = await count(Case)
    chats = await count(Chat)

    await _edit(
        callback,
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: <b>{users}</b>\n"
        f"💰 Кошельков: <b>{wallets}</b>\n"
        f"📜 Транзакций: <b>{transactions}</b>\n"
        f"🧬 Персонажей: <b>{characters}</b>\n"
        f"🧬 Рас: <b>{races}</b>\n"
        f"🏅 Рангов: <b>{ranks}</b>\n"
        f"✨ Способностей: <b>{abilities}</b>\n"
        f"🛍 Предметов: <b>{items}</b>\n"
        f"🎁 Кейсов: <b>{cases}</b>\n"
        f"💬 Чатов: <b>{chats}</b>",
        founder_main_keyboard(),
    )


# ============================================================================
# FALLBACK FOR EXISTING USER ACTIONS
# ============================================================================


@router.callback_query(
    F.data.startswith("founder:user:rank:")
)
async def founder_user_rank_view(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    user_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    character = await CharacterRepository(
        session
    ).get_character(user_id)

    if character is None:
        await _edit(
            callback,
            "❌ У пользователя нет персонажа.",
            founder_users_keyboard(),
        )
        return

    await _edit(
        callback,
        "🏅 <b>Ранг персонажа</b>\n\n"
        f"User ID: <code>{user_id}</code>\n"
        f"Rank ID: <code>{character.rank_id or '-'}</code>",
        founder_user_actions_keyboard(
            user_id
        ),
    )


@router.callback_query(
    F.data.startswith("founder:user:abilities:")
)
async def founder_user_abilities_view(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    user_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    repo = CharacterRepository(
        session
    )

    abilities = await repo.get_character_abilities(
        user_id
    )

    if not abilities:
        text = (
            "✨ <b>Способности пользователя</b>\n\n"
            "Способностей нет."
        )
    else:
        text = (
            "✨ <b>Способности пользователя</b>\n\n"
            + "\n".join(
                f"• Ability ID: "
                f"<code>{item.ability_id}</code>"
                for item in abilities
            )
        )

    await _edit(
        callback,
        text,
        founder_user_actions_keyboard(
            user_id
        ),
    )


@router.callback_query(
    F.data.startswith("founder:user:inventory:")
)
async def founder_user_inventory_view(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    user_id = int(
        (callback.data or "").rsplit(
            ":",
            1,
        )[1]
    )

    items = await InventoryRepository(
        session
    ).get_inventory(
        user_id
    )

    if not items:
        text = (
            "🎒 <b>Инвентарь</b>\n\n"
            "Инвентарь пуст."
        )
    else:
        text = (
            "🎒 <b>Инвентарь</b>\n\n"
            + "\n".join(
                f"• Item ID "
                f"<code>{item.item_id}</code>: "
                f"{item.quantity} шт."
                for item in items
            )
        )

    await _edit(
        callback,
        text,
        founder_user_actions_keyboard(
            user_id
        ),
    )


# ============================================================================
# GENERIC NAVIGATION
# ============================================================================


@router.callback_query(
    F.data == "founder:chats"
)
async def founder_chats_again(
    callback: CallbackQuery,
) -> None:
    await _edit(
        callback,
        "💬 <b>Чаты</b>",
        founder_chats_keyboard(),
    )