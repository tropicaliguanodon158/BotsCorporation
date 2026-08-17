"""
Quest/task service.

Работает с Task и UserTask.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.tasks import Task, UserTask
from app.services.rewards import RewardsService


class QuestsService:
    """
    Сервис заданий.

    Поддерживает:
        - получение задания;
        - создание прогресса;
        - увеличение прогресса;
        - завершение;
        - получение награды.
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
    # TASK
    # ========================================================================

    async def get_task(
        self,
        *,
        task_id: int,
    ) -> Task | None:
        result = await self.session.execute(
            select(Task).where(
                Task.id == task_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_active_tasks(
        self,
    ) -> list[Task]:
        result = await self.session.execute(
            select(Task)
            .where(
                Task.is_active.is_(True),
            )
            .order_by(
                Task.id.asc(),
            )
        )

        return list(result.scalars().all())

    # ========================================================================
    # USER TASK
    # ========================================================================

    async def get_user_task(
        self,
        *,
        user_id: int,
        task_id: int,
        period_date: date | None = None,
    ) -> UserTask | None:
        query = select(UserTask).where(
            UserTask.user_id == user_id,
            UserTask.task_id == task_id,
        )

        if period_date is None:
            query = query.where(
                UserTask.period_date.is_(None),
            )
        else:
            query = query.where(
                UserTask.period_date == period_date,
            )

        result = await self.session.execute(query)

        return result.scalar_one_or_none()

    async def ensure_user_task(
        self,
        *,
        user_id: int,
        task_id: int,
        period_date: date | None = None,
    ) -> UserTask:
        user_task = await self.get_user_task(
            user_id=user_id,
            task_id=task_id,
            period_date=period_date,
        )

        if user_task is not None:
            return user_task

        user_task = UserTask(
            user_id=user_id,
            task_id=task_id,
            progress=0,
            period_date=period_date,
        )

        self.session.add(user_task)

        await self.session.flush()

        return user_task

    # ========================================================================
    # PROGRESS
    # ========================================================================

    async def add_progress(
        self,
        *,
        user_id: int,
        task_id: int,
        amount: int = 1,
        period_date: date | None = None,
    ) -> UserTask:
        if amount <= 0:
            raise ValueError(
                "Progress amount must be greater than zero."
            )

        task = await self.get_task(
            task_id=task_id,
        )

        if task is None:
            raise ValueError(
                "Task does not exist."
            )

        if not task.is_active:
            raise ValueError(
                "Task is inactive."
            )

        user_task = await self.ensure_user_task(
            user_id=user_id,
            task_id=task_id,
            period_date=period_date,
        )

        if user_task.completed_at is not None:
            return user_task

        user_task.progress = min(
            user_task.progress + amount,
            task.target_value,
        )

        if user_task.progress >= task.target_value:
            user_task.progress = task.target_value
            user_task.completed_at = datetime.now()

        await self.session.flush()

        return user_task

    # ========================================================================
    # CLAIM
    # ========================================================================

    async def claim_reward(
        self,
        *,
        user_id: int,
        task_id: int,
        chat_id: int | None = None,
        period_date: date | None = None,
    ) -> UserTask:
        task = await self.get_task(
            task_id=task_id,
        )

        if task is None:
            raise ValueError(
                "Task does not exist."
            )

        user_task = await self.get_user_task(
            user_id=user_id,
            task_id=task_id,
            period_date=period_date,
        )

        if user_task is None:
            raise ValueError(
                "Task progress does not exist."
            )

        if user_task.completed_at is None:
            raise ValueError(
                "Task is not completed."
            )

        if user_task.claimed_at is not None:
            raise ValueError(
                "Task reward has already been claimed."
            )

        await self.rewards.custom_reward(
            user_id=user_id,
            chat_id=chat_id,
            currency=task.reward_currency,
            xp=task.reward_xp,
            gems=task.reward_gems,
            source=f"task:{task.id}",
        )

        user_task.claimed_at = datetime.now()

        await self.session.flush()

        return user_task