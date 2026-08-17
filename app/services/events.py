from __future__ import annotations

from datetime import date, datetime

from app.database.repositories.tasks import TasksRepository
from app.database.repositories.users import UserRepository


class EventsService:
    """
    Центральная обработка игровых и пользовательских событий.

    Важно:
        commit()/rollback() выполняет DatabaseMiddleware.

    Сервис не обращается к Telegram API.
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
        xp: int = 0,
    ):
        """
        Обрабатывает обычное сообщение.

        Изменяет:
            - общий счётчик сообщений;
            - дневной счётчик;
            - дневную активность;
            - XP.

        Возвращает уже обновлённого пользователя.

        Все изменения находятся в одной SQLAlchemy session.
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

        # ====================================================================
        # MESSAGE COUNTERS
        # ====================================================================

        user.message_count += 1
        user.daily_message_count += 1

        # ====================================================================
        # DAILY ACTIVITY
        # ====================================================================

        if self.tasks_repository is not None:
            await self.tasks_repository.increment_daily_activity(
                user_id=user_id,
                activity_date=(
                    activity_date
                    or datetime.now().date()
                ),
                message_type=message_type,
            )

        # ====================================================================
        # XP
        # ====================================================================

        if xp > 0:
            user.xp += xp

        # Изменения уже находятся в session.
        # Отдельные UPDATE + повторный SELECT здесь не нужны.

        await self.user_repository.session.flush()

        return user

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
            user.xp += xp

        if reputation != 0:
            user.reputation += reputation

        await self.user_repository.session.flush()

        return user

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
            user.xp += xp

        if reputation != 0:
            user.reputation += reputation

        await self.user_repository.session.flush()

        return user
