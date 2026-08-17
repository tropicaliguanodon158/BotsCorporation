
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


def create_rewards_service(session) -> RewardsService:
    return RewardsService(
        economy_repository=EconomyRepository(session),
        settings_repository=SettingsRepository(session),
        user_repository=UserRepository(session),
    )


# ============================================================================
# HOURLY
# ============================================================================


@router.message(Command("hourly"))
async def hourly_handler(
    message: Message,
    session,
) -> None:
    if message.from_user is None:
        return

    service = create_rewards_service(session)

    result = await service.hourly_reward(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
    )

    if not result.rewarded:
        if result.reason == "cooldown":
            await message.answer(
                "⏰ Часовую награду можно получать "
                "не чаще одного раза в час."
            )
            return

        await message.answer(
            "❌ Часовая награда сейчас недоступна."
        )
        return

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
    if message.from_user is None:
        return

    service = create_rewards_service(session)

    result = await service.daily_reward(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
    )

    if not result.rewarded:
        if result.reason == "already_claimed":
            await message.answer(
                "🎁 Ежедневная награда уже получена сегодня.\n"
                "Возвращайся завтра."
            )
            return

        await message.answer(
            "❌ Ежедневная награда сейчас недоступна."
        )
        return

    await message.answer(
        "🎁 <b>Ежедневная награда</b>\n\n"
        f"💵 +{result.currency:.2f}\n"
        f"⭐ +{result.xp} XP\n"
        f"💎 +{result.gems}"
    )