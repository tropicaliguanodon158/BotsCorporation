from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from app.database.models.tasks import UserDailyActivity
from app.database.repositories.users import UserRepository


class EventsService:
    """
    Центральная обработка игровых событий пользователя.

    Используется handlers/middlewares.

    Здесь НЕ отправляются Telegram-сообщения.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        daily_activity_repository=None,
    ) -> None:
        self.user_repository = user_repository
        self.daily_activity_repository = (
            daily_activity_repository
        )

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
            await self.user_repository.update_profile(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
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
        xp: int = 1,
    ):
        """
        Обработать одно сообщение пользователя.

        Важный принцип:
            никаких ответных сообщений здесь нет.

        Это позволяет начислять экономику/XP молча.
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

        await self.user_repository.increment_message_count(
            user_id,
        )

        await self.user_repository.increment_daily_message_count(
            user_id,
        )

        if xp > 0:
            await self.user_repository.add_xp(
                user_id,
                xp,
            )

        return await self.user_repository.get_by_id(
            user_id,
        )

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
            user_id,
            amount,
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
            user_id,
            amount,
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
            user_id,
        )

    # ========================================================================
    # SIMPLE EVENT HELPERS
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

        if xp:
            await self.user_repository.add_xp(
                user_id,
                xp,
            )

        if reputation:
            await self.user_repository.add_reputation(
                user_id,
                reputation,
            )

        return await self.user_repository.get_by_id(
            user_id,
        )

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

        if xp:
            await self.user_repository.add_xp(
                user_id,
                xp,
            )

        if reputation:
            await self.user_repository.add_reputation(
                user_id,
                reputation,
            )

        return await self.user_repository.get_by_id(
            user_id,
        )