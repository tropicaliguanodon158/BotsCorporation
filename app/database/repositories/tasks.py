from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.tasks import (
    Achievement,
    Task,
    UserAchievement,
    UserDailyActivity,
    UserTask,
)


class TasksRepository:
    """
    Repository для системы активности, заданий и достижений.

    Работает с моделями:

        UserDailyActivity
        Task
        UserTask
        Achievement
        UserAchievement

    Здесь только работа с БД.
    Бизнес-логика находится в services/quests.py,
    services/achivements.py и services/events.py.

    commit() здесь намеренно не выполняется.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ========================================================================
    # DAILY ACTIVITY
    # ========================================================================

    async def get_daily_activity(
        self,
        *,
        user_id: int,
        activity_date: date,
    ) -> UserDailyActivity | None:
        """
        Получить дневную активность пользователя.
        """

        result = await self.session.execute(
            select(UserDailyActivity).where(
                UserDailyActivity.user_id == user_id,
                UserDailyActivity.activity_date == activity_date,
            )
        )

        return result.scalar_one_or_none()

    async def get_or_create_daily_activity(
        self,
        *,
        user_id: int,
        activity_date: date,
    ) -> UserDailyActivity:
        """
        Получить или создать запись дневной активности.
        """

        activity = await self.get_daily_activity(
            user_id=user_id,
            activity_date=activity_date,
        )

        if activity is not None:
            return activity

        activity = UserDailyActivity(
            user_id=user_id,
            activity_date=activity_date,
        )

        self.session.add(activity)

        await self.session.flush()

        return activity

    async def increment_daily_activity(
        self,
        *,
        user_id: int,
        activity_date: date,
        message_type: str = "text",
        earned_currency: Decimal | int | float | str = Decimal("0.00"),
        spent_currency: Decimal | int | float | str = Decimal("0.00"),
    ) -> UserDailyActivity:
        """
        Зафиксировать активность пользователя за день.

        message_type:

            text
            photo
            video
            other
        """

        activity = await self.get_or_create_daily_activity(
            user_id=user_id,
            activity_date=activity_date,
        )

        activity.messages_count += 1

        message_type = message_type.strip().lower()

        if message_type == "text":
            activity.text_messages += 1

        elif message_type == "photo":
            activity.photo_messages += 1

        elif message_type == "video":
            activity.video_messages += 1

        else:
            activity.other_messages += 1

        earned = Decimal(str(earned_currency)).quantize(
            Decimal("0.01")
        )

        spent = Decimal(str(spent_currency)).quantize(
            Decimal("0.01")
        )

        if earned < 0:
            raise ValueError(
                "earned_currency cannot be negative."
            )

        if spent < 0:
            raise ValueError(
                "spent_currency cannot be negative."
            )

        activity.earned_currency += earned
        activity.spent_currency += spent

        activity.last_activity_at = datetime.now()

        await self.session.flush()

        return activity

    async def add_active_minutes(
        self,
        *,
        user_id: int,
        activity_date: date,
        minutes: int,
    ) -> UserDailyActivity:
        """
        Добавить активные минуты.
        """

        if minutes <= 0:
            raise ValueError(
                "minutes must be greater than zero."
            )

        activity = await self.get_or_create_daily_activity(
            user_id=user_id,
            activity_date=activity_date,
        )

        activity.active_minutes += minutes
        activity.last_activity_at = datetime.now()

        await self.session.flush()

        return activity

    async def get_activity_for_period(
        self,
        *,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> Sequence[UserDailyActivity]:
        """
        Получить активность пользователя за период.
        """

        if end_date < start_date:
            raise ValueError(
                "end_date cannot be earlier than start_date."
            )

        result = await self.session.execute(
            select(UserDailyActivity)
            .where(
                UserDailyActivity.user_id == user_id,
                UserDailyActivity.activity_date >= start_date,
                UserDailyActivity.activity_date <= end_date,
            )
            .order_by(
                UserDailyActivity.activity_date.asc(),
            )
        )

        return result.scalars().all()

    async def get_message_count_for_period(
        self,
        *,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> int:
        """
        Получить суммарное количество сообщений
        за период.
        """

        activities = await self.get_activity_for_period(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        return sum(
            activity.messages_count
            for activity in activities
        )

    # ========================================================================
    # TASKS
    # ========================================================================

    async def get_task(
        self,
        task_id: int,
    ) -> Task | None:
        """
        Получить задание по ID.
        """

        result = await self.session.execute(
            select(Task).where(
                Task.id == task_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_task_by_name(
        self,
        name: str,
    ) -> Task | None:
        """
        Получить задание по названию.
        """

        result = await self.session.execute(
            select(Task).where(
                Task.name == name,
            )
        )

        return result.scalar_one_or_none()

    async def get_active_tasks(
        self,
        *,
        task_type: str | None = None,
        task_period: str | None = None,
    ) -> Sequence[Task]:
        """
        Получить активные задания.
        """

        query = select(Task).where(
            Task.is_active.is_(True),
        )

        if task_type is not None:
            query = query.where(
                Task.task_type == task_type,
            )

        if task_period is not None:
            query = query.where(
                Task.task_period == task_period,
            )

        query = query.order_by(
            Task.id.asc(),
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    async def create_task(
        self,
        *,
        name: str,
        description: str = "",
        task_type: str,
        target_value: int = 1,
        reward_currency: Decimal | int | float | str = Decimal("0.00"),
        reward_xp: int = 0,
        reward_gems: int = 0,
        reward_item_id: int | None = None,
        task_period: str = "daily",
        is_active: bool = True,
    ) -> Task:
        """
        Создать задание.
        """

        if not name.strip():
            raise ValueError(
                "Task name cannot be empty."
            )

        if not task_type.strip():
            raise ValueError(
                "Task type cannot be empty."
            )

        if target_value <= 0:
            raise ValueError(
                "Task target_value must be greater than zero."
            )

        reward_currency = Decimal(
            str(reward_currency)
        ).quantize(
            Decimal("0.01")
        )

        if reward_currency < 0:
            raise ValueError(
                "Task reward_currency cannot be negative."
            )

        if reward_xp < 0:
            raise ValueError(
                "Task reward_xp cannot be negative."
            )

        if reward_gems < 0:
            raise ValueError(
                "Task reward_gems cannot be negative."
            )

        task = Task(
            name=name.strip(),
            description=description,
            task_type=task_type.strip(),
            target_value=target_value,
            reward_currency=reward_currency,
            reward_xp=reward_xp,
            reward_gems=reward_gems,
            reward_item_id=reward_item_id,
            task_period=task_period,
            is_active=is_active,
        )

        self.session.add(task)

        await self.session.flush()

        return task

    async def update_task(
        self,
        task_id: int,
        **values: object,
    ) -> Task | None:
        """
        Изменить задание.
        """

        allowed_fields = {
            "name",
            "description",
            "task_type",
            "target_value",
            "reward_currency",
            "reward_xp",
            "reward_gems",
            "reward_item_id",
            "task_period",
            "is_active",
        }

        invalid_fields = set(values) - allowed_fields

        if invalid_fields:
            raise ValueError(
                "Unsupported task fields: "
                + ", ".join(sorted(invalid_fields))
            )

        task = await self.get_task(task_id)

        if task is None:
            return None

        if "name" in values:
            name = str(values["name"]).strip()

            if not name:
                raise ValueError(
                    "Task name cannot be empty."
                )

            values["name"] = name

        if "task_type" in values:
            task_type = str(
                values["task_type"]
            ).strip()

            if not task_type:
                raise ValueError(
                    "Task type cannot be empty."
                )

            values["task_type"] = task_type

        if "target_value" in values:
            target = int(
                values["target_value"]
            )

            if target <= 0:
                raise ValueError(
                    "Task target_value must be greater than zero."
                )

            values["target_value"] = target

        if "reward_currency" in values:
            reward = Decimal(
                str(values["reward_currency"])
            ).quantize(
                Decimal("0.01")
            )

            if reward < 0:
                raise ValueError(
                    "Task reward_currency cannot be negative."
                )

            values["reward_currency"] = reward

        if "reward_xp" in values:
            xp = int(values["reward_xp"])

            if xp < 0:
                raise ValueError(
                    "Task reward_xp cannot be negative."
                )

            values["reward_xp"] = xp

        if "reward_gems" in values:
            gems = int(values["reward_gems"])

            if gems < 0:
                raise ValueError(
                    "Task reward_gems cannot be negative."
                )

            values["reward_gems"] = gems

        for field, value in values.items():
            setattr(task, field, value)

        await self.session.flush()

        return task

    # ========================================================================
    # USER TASKS
    # ========================================================================

    async def get_user_task(
        self,
        *,
        user_id: int,
        task_id: int,
        period_date: date | None = None,
    ) -> UserTask | None:
        """
        Получить прогресс пользователя по заданию.

        Для повторяемых заданий можно дополнительно
        указать дату периода.
        """

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

    async def get_or_create_user_task(
        self,
        *,
        user_id: int,
        task_id: int,
        period_date: date | None = None,
    ) -> UserTask:
        """
        Получить или создать прогресс задания.
        """

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
            period_date=period_date,
        )

        self.session.add(user_task)

        await self.session.flush()

        return user_task

    async def update_task_progress(
        self,
        *,
        user_id: int,
        task_id: int,
        amount: int = 1,
        period_date: date | None = None,
    ) -> UserTask:
        """
        Увеличить прогресс задания.

        Ограничение target_value будет применять service-слой.
        """

        if amount <= 0:
            raise ValueError(
                "Progress amount must be greater than zero."
            )

        task = await self.get_task(task_id)

        if task is None:
            raise ValueError(
                f"Task {task_id} does not exist."
            )

        user_task = await self.get_or_create_user_task(
            user_id=user_id,
            task_id=task_id,
            period_date=period_date,
        )

        user_task.progress += amount

        if (
            user_task.progress >= task.target_value
            and user_task.completed_at is None
        ):
            user_task.completed_at = datetime.now()

        await self.session.flush()

        return user_task

    async def get_user_tasks(
        self,
        *,
        user_id: int,
        period_date: date | None = None,
        completed: bool | None = None,
    ) -> Sequence[UserTask]:
        """
        Получить задания пользователя.
        """

        query = select(UserTask).where(
            UserTask.user_id == user_id,
        )

        if period_date is not None:
            query = query.where(
                UserTask.period_date == period_date,
            )

        if completed is True:
            query = query.where(
                UserTask.completed_at.is_not(None),
            )

        elif completed is False:
            query = query.where(
                UserTask.completed_at.is_(None),
            )

        query = query.order_by(
            UserTask.id.asc(),
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    async def claim_task(
        self,
        *,
        user_id: int,
        task_id: int,
        period_date: date | None = None,
    ) -> UserTask | None:
        """
        Пометить выполненное задание как полученное.

        Проверка награды и фактическая выдача выполняются
        service-слоем.
        """

        user_task = await self.get_user_task(
            user_id=user_id,
            task_id=task_id,
            period_date=period_date,
        )

        if user_task is None:
            return None

        if user_task.completed_at is None:
            return None

        if user_task.claimed_at is not None:
            return None

        user_task.claimed_at = datetime.now()

        await self.session.flush()

        return user_task

    # ========================================================================
    # ACHIEVEMENTS
    # ========================================================================

    async def get_achievement(
        self,
        achievement_id: int,
    ) -> Achievement | None:
        """
        Получить достижение по ID.
        """

        result = await self.session.execute(
            select(Achievement).where(
                Achievement.id == achievement_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_achievement_by_name(
        self,
        name: str,
    ) -> Achievement | None:
        """
        Получить достижение по названию.
        """

        result = await self.session.execute(
            select(Achievement).where(
                Achievement.name == name,
            )
        )

        return result.scalar_one_or_none()

    async def get_active_achievements(
        self,
        *,
        condition_type: str | None = None,
    ) -> Sequence[Achievement]:
        """
        Получить активные достижения.
        """

        query = select(Achievement).where(
            Achievement.is_active.is_(True),
        )

        if condition_type is not None:
            query = query.where(
                Achievement.condition_type == condition_type,
            )

        query = query.order_by(
            Achievement.id.asc(),
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    async def create_achievement(
        self,
        *,
        name: str,
        description: str = "",
        condition_type: str,
        condition_value: int = 1,
        reward_currency: Decimal | int | float | str = Decimal("0.00"),
        reward_xp: int = 0,
        reward_gems: int = 0,
        reward_item_id: int | None = None,
        is_active: bool = True,
    ) -> Achievement:
        """
        Создать достижение.
        """

        if not name.strip():
            raise ValueError(
                "Achievement name cannot be empty."
            )

        if not condition_type.strip():
            raise ValueError(
                "Achievement condition_type cannot be empty."
            )

        if condition_value <= 0:
            raise ValueError(
                "Achievement condition_value must be greater than zero."
            )

        reward_currency = Decimal(
            str(reward_currency)
        ).quantize(
            Decimal("0.01")
        )

        if reward_currency < 0:
            raise ValueError(
                "Achievement reward_currency cannot be negative."
            )

        if reward_xp < 0:
            raise ValueError(
                "Achievement reward_xp cannot be negative."
            )

        if reward_gems < 0:
            raise ValueError(
                "Achievement reward_gems cannot be negative."
            )

        achievement = Achievement(
            name=name.strip(),
            description=description,
            condition_type=condition_type.strip(),
            condition_value=condition_value,
            reward_currency=reward_currency,
            reward_xp=reward_xp,
            reward_gems=reward_gems,
            reward_item_id=reward_item_id,
            is_active=is_active,
        )

        self.session.add(achievement)

        await self.session.flush()

        return achievement

    # ========================================================================
    # USER ACHIEVEMENTS
    # ========================================================================

    async def get_user_achievement(
        self,
        *,
        user_id: int,
        achievement_id: int,
    ) -> UserAchievement | None:
        """
        Проверить, получил ли пользователь достижение.
        """

        result = await self.session.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id,
            )
        )

        return result.scalar_one_or_none()

    async def has_achievement(
        self,
        *,
        user_id: int,
        achievement_id: int,
    ) -> bool:
        """
        Проверить наличие достижения у пользователя.
        """

        return (
            await self.get_user_achievement(
                user_id=user_id,
                achievement_id=achievement_id,
            )
        ) is not None

    async def unlock_achievement(
        self,
        *,
        user_id: int,
        achievement_id: int,
    ) -> UserAchievement:
        """
        Выдать достижение пользователю.

        Если достижение уже существует,
        выбрасывается ValueError.
        """

        existing = await self.get_user_achievement(
            user_id=user_id,
            achievement_id=achievement_id,
        )

        if existing is not None:
            raise ValueError(
                "User already has this achievement."
            )

        achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement_id,
        )

        self.session.add(achievement)

        await self.session.flush()

        return achievement

    async def get_user_achievements(
        self,
        user_id: int,
    ) -> Sequence[UserAchievement]:
        """
        Получить все достижения пользователя.
        """

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

        return result.scalars().all()