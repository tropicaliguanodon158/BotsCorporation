from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.database.repositories.tasks import TasksRepository
from app.database.repositories.users import UserRepository


class EventsService:
    """
    Центральная обработка событий пользователя.

    Отвечает за:
        - регистрацию пользователя;
        - обработку сообщений;
        - статистику ежедневной активности;
        - XP;
        - репутацию;
        - игровые события.

    Telegram API здесь не используется.

    commit()/rollback() выполняет DatabaseMiddleware.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        tasks_repository: TasksRepository | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.tasks_repository = tasks_repository

    # ========================================================================
    # USER
    # ========================================================================

    async def ensure_user(
        self,
        *,
        user_id: int,
        first_name: str,
        last_name: str | None = None,
        username: str | None = None,
    ):
        user, created = await self.user_repository.get_or_create(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )

        if not created:
            user = await self.user_repository.update_profile(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
            )

            if user is None:
                raise RuntimeError(
                    "User disappeared while updating profile."
                )

        return user, created

    # ========================================================================
    # MESSAGE
    # ========================================================================

    async def on_message(
        self,
        *,
        user_id: int,
        message_type: str = "text",
        activity_date: date | None = None,
        xp: int = 1,
    ):
        """
        Обработать сообщение пользователя.

        Изменяет:
            - общий счётчик сообщений;
            - дневной счётчик;
            - UserDailyActivity;
            - XP.

        Никаких сообщений пользователю здесь не отправляется.
        """

        user = await self.user_repository.get_by_id(
            user_id,
        )

        if user is None:
            raise ValueError(
                "User does not exist."
            )

        if not user.is_active:
            return user

        message_type = (
            message_type.strip().lower()
        )

        if message_type not in {
            "text",
            "photo",
            "video",
            "other",
        }:
            message_type = "other"

        await self.user_repository.increment_message_count(
            user_id=user_id,
        )

        await self.user_repository.increment_daily_message_count(
            user_id=user_id,
        )

        if self.tasks_repository is not None:
            await self.tasks_repository.increment_daily_activity(
                user_id=user_id,
                activity_date=(
                    activity_date
                    or datetime.now().date()
                ),
                message_type=message_type,
            )

        if xp > 0:
            await self.user_repository.add_xp(
                user_id=user_id,
                amount=xp,
            )

        result = await self.user_repository.get_by_id(
            user_id,
        )

        if result is None:
            raise RuntimeError(
                "User disappeared after message processing."
            )

        return result

    # ========================================================================
    # XP
    # ========================================================================

    async def add_xp(
        self,
        *,
        user_id: int,
        amount: int,
    ):
        if amount <= 0:
            raise ValueError(
                "XP amount must be greater than zero."
            )

        return await self.user_repository.add_xp(
            user_id=user_id,
            amount=amount,
        )

    # ========================================================================
    # REPUTATION
    # ========================================================================

    async def add_reputation(
        self,
        *,
        user_id: int,
        amount: int,
    ):
        if amount == 0:
            return await self.user_repository.get_by_id(
                user_id,
            )

        return await self.user_repository.add_reputation(
            user_id=user_id,
            amount=amount,
        )

    # ========================================================================
    # DAILY RESET
    # ========================================================================

    async def reset_daily_activity(
        self,
        *,
        user_id: int,
    ):
        return await self.user_repository.reset_daily_message_count(
            user_id=user_id,
        )

    # ========================================================================
    # GAME WIN
    # ========================================================================

    async def on_game_win(
        self,
        *,
        user_id: int,
        xp: int = 10,
        reputation: int = 1,
    ):
        user = await self.user_repository.get_by_id(
            user_id,
        )

        if user is None:
            raise ValueError(
                "User does not exist."
            )

        if xp > 0:
            await self.user_repository.add_xp(
                user_id=user_id,
                amount=xp,
            )

        if reputation != 0:
            await self.user_repository.add_reputation(
                user_id=user_id,
                amount=reputation,
            )

        return await self.user_repository.get_by_id(
            user_id,
        )

    # ========================================================================
    # GAME LOSS
    # ========================================================================

    async def on_game_loss(
        self,
        *,
        user_id: int,
        xp: int = 2,
        reputation: int = 0,
    ):
        user = await self.user_repository.get_by_id(
            user_id,
        )

        if user is None:
            raise ValueError(
                "User does not exist."
            )

        if xp > 0:
            await self.user_repository.add_xp(
                user_id=user_id,
                amount=xp,
            )

        if reputation != 0:
            await self.user_repository.add_reputation(
                user_id=user_id,
                amount=reputation,
            )

        return await self.user_repository.get_by_id(
            user_id,
        )