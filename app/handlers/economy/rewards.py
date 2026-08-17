from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.repositories.economy import EconomyRepository
from app.database.repositories.settings import SettingsRepository
from app.database.repositories.users import UserRepository
from app.services.rewards import RewardsService


router = Router(
    name="economy_rewards",
)


# ============================================================================
# COMMANDS
# ============================================================================


@router.message(Command("hourly"))
async def hourly_handler(
    message: Message,
    session,
) -> None:
    """
    Выдать часовую награду.

    Cooldown пока намеренно не добавляем:
    он будет подключён отдельным этапом через существующий
    cooldown utility/service.
    """

    if message.from_user is None:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    economy_repository = EconomyRepository(
        session,
    )

    settings_repository = SettingsRepository(
        session,
    )

    user_repository = UserRepository(
        session,
    )

    service = RewardsService(
        economy_repository=economy_repository,
        settings_repository=settings_repository,
        user_repository=user_repository,
    )

    result = await service.hourly_reward(
        user_id=user_id,
        chat_id=chat_id,
    )

    await message.answer(
        "⏰ <b>Часовая награда</b>\n\n"
        f"💵 +{result.currency:.2f}\n"
        f"⭐ +{result.xp} XP\n"
        f"💎 +{result.gems}"
    )


@router.message(Command("daily"))
async def daily_handler(
    message: Message,
    session,
) -> None:
    """
    Выдать ежедневную награду.

    Защита от повторного получения будет добавлена
    через activity/reward tracking.
    """

    if message.from_user is None:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    economy_repository = EconomyRepository(
        session,
    )

    settings_repository = SettingsRepository(
        session,
    )

    user_repository = UserRepository(
        session,
    )

    service = RewardsService(
        economy_repository=economy_repository,
        settings_repository=settings_repository,
        user_repository=user_repository,
    )

    result = await service.daily_reward(
        user_id=user_id,
        chat_id=chat_id,
    )

    await message.answer(
        "🎁 <b>Ежедневная награда</b>\n\n"
        f"💵 +{result.currency:.2f}\n"
        f"⭐ +{result.xp} XP\n"
        f"💎 +{result.gems}"
    )


# ============================================================================
# PASSIVE MESSAGE REWARD
# ============================================================================


@router.message(
    F.chat.type.in_(
        {
            "group",
            "supergroup",
        }
    )
)
async def message_reward_handler(
    message: Message,
    session,
) -> None:
    """
    Автоматическая награда за активность в чате.

    Команды не награждаются.

    Одновременно обновляются:
        - общий счётчик сообщений;
        - дневной счётчик;
        - баланс;
        - XP;
        - гемы.

    Бот ничего не отвечает на обычное сообщение.
    """

    if message.from_user is None:
        return

    # ------------------------------------------------------------------------
    # Не награждаем команды.
    # ------------------------------------------------------------------------

    if message.text and message.text.startswith("/"):
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    # ------------------------------------------------------------------------
    # Определяем тип сообщения.
    # ------------------------------------------------------------------------

    if message.photo:
        message_type = "photo"

    elif message.video:
        message_type = "video"

    elif message.text:
        message_type = "text"

    else:
        message_type = "other"

    # ------------------------------------------------------------------------
    # Repositories.
    # ------------------------------------------------------------------------

    users = UserRepository(
        session,
    )

    economy = EconomyRepository(
        session,
    )

    settings = SettingsRepository(
        session,
    )

    # ------------------------------------------------------------------------
    # Гарантируем существование чата.
    # ------------------------------------------------------------------------

    await settings.get_or_create_chat(
        chat_id=chat_id,
        title=message.chat.title,
        username=message.chat.username,
        chat_type=message.chat.type,
    )

    # ------------------------------------------------------------------------
    # Обновляем статистику пользователя.
    # ------------------------------------------------------------------------

    await users.increment_message_count(
        user_id=user_id,
    )

    await users.increment_daily_message_count(
        user_id=user_id,
    )

    # ------------------------------------------------------------------------
    # Выдаём награду.
    # ------------------------------------------------------------------------

    service = RewardsService(
        economy_repository=economy,
        settings_repository=settings,
        user_repository=users,
    )

    await service.message_reward(
        user_id=user_id,
        chat_id=chat_id,
        message_type=message_type,
    )