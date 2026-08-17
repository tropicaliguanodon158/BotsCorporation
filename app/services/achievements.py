"""
Achievements service.

Работа с долгосрочными достижениями пользователя.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.tasks import (
    Achievement,
    UserAchievement,
)
from app.services.rewards import RewardsService


@dataclass(slots=True)
class AchievementResult:
    achievement: Achievement
    unlocked: bool
    already_unlocked: bool = False


class AchievementsService:
    """
    Сервис достижений.

    SQL находится только здесь, потому что отдельного
    AchievementRepository в утверждённой архитектуре пока нет.
    """

    def __init__(
        self,
        *,
        session: AsyncSession,
        rewards_service: RewardsService,
    ) -> None:
        self.session = session
        self.rewards = rewards_service

    # ========================================================================
    # GET
    # ========================================================================

    async def get_achievement(
        self,
        *,
        achievement_id: int,
    ) -> Achievement | None:
        result = await self.session.execute(
            select(Achievement).where(
                Achievement.id == achievement_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_user_achievements(
        self,
        *,
        user_id: int,
    ) -> list[UserAchievement]:
        result = await self.session.execute(
            select(UserAchievement)
            .where(
                UserAchievement.user_id == user_id,
            )
            .order_by(
                UserAchievement.unlocked_at.asc(),
                UserAchievement.id.asc(),
            )
        )

        return list(result.scalars().all())

    # ========================================================================
    # CHECK
    # ========================================================================

    async def is_unlocked(
        self,
        *,
        user_id: int,
        achievement_id: int,
    ) -> bool:
        result = await self.session.execute(
            select(UserAchievement.id).where(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id,
            )
        )

        return result.scalar_one_or_none() is not None

    # ========================================================================
    # UNLOCK
    # ========================================================================

    async def unlock(
        self,
        *,
        user_id: int,
        achievement_id: int,
        chat_id: int | None = None,
    ) -> AchievementResult:
        achievement = await self.get_achievement(
            achievement_id=achievement_id,
        )

        if achievement is None:
            raise ValueError(
                "Achievement does not exist."
            )

        if not achievement.is_active:
            raise ValueError(
                "Achievement is inactive."
            )

        already_unlocked = await self.is_unlocked(
            user_id=user_id,
            achievement_id=achievement_id,
        )

        if already_unlocked:
            return AchievementResult(
                achievement=achievement,
                unlocked=False,
                already_unlocked=True,
            )

        record = UserAchievement(
            user_id=user_id,
            achievement_id=achievement_id,
            unlocked_at=datetime.now(),
        )

        self.session.add(record)

        await self.session.flush()

        if (
            achievement.reward_currency > 0
            or achievement.reward_xp > 0
            or achievement.reward_gems > 0
        ):
            await self.rewards.custom_reward(
                user_id=user_id,
                chat_id=chat_id,
                currency=achievement.reward_currency,
                xp=achievement.reward_xp,
                gems=achievement.reward_gems,
                source=f"achievement:{achievement.id}",
            )

        return AchievementResult(
            achievement=achievement,
            unlocked=True,
        )