from __future__ import annotations

from aiogram import Router
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
# HOURLY
# ============================================================================


@router.message(Command("hourly"))
async def hourly_handler(
    message: Message,
    session,
) -> None:
    """
    Выдать часовую награду.

    Проверка cooldown будет добавлена
    отдельным этапом.
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


# ============================================================================
# DAILY
# ============================================================================


@router.message(Command("daily"))
async def daily_handler(
    message: Message,
    session,
) -> None:
    """
    Выдать ежедневную награду.

    Защита от повторного получения будет
    подключена отдельным этапом.
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