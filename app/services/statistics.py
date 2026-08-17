from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.database.repositories.economy import EconomyRepository
from app.database.repositories.users import UserRepository


@dataclass(slots=True)
class UserStatistics:
    user_id: int

    level: int
    xp: int
    reputation: int

    message_count: int
    daily_message_count: int

    balance: Decimal
    gems: int


class StatisticsService:
    """
    Сервис пользовательской статистики.

    Отвечает только за сбор и подготовку статистических данных.

    Repository:
        UserRepository
            - профиль;
            - уровень;
            - XP;
            - репутация;
            - активность.

        EconomyRepository
            - баланс;
            - гемы.

    Telegram API здесь не используется.
    commit()/rollback() здесь не выполняются.
    """

    def __init__(
        self,
        *,
        user_repository: UserRepository,
        economy_repository: EconomyRepository,
    ) -> None:
        self.users = user_repository
        self.economy = economy_repository

    # ========================================================================
    # USER STATISTICS
    # ========================================================================

    async def get_user_statistics(
        self,
        *,
        user_id: int,
    ) -> UserStatistics:
        """
        Получить полную статистику пользователя.
        """

        if user_id <= 0:
            raise ValueError("Invalid user_id.")

        user = await self.users.get_by_id(
            user_id,
        )

        if user is None:
            raise ValueError(
                f"User {user_id} does not exist."
            )

        balance = await self.economy.get_balance(
            user_id,
        )

        gems = await self.economy.get_gems(
            user_id,
        )

        return UserStatistics(
            user_id=user.id,
            level=user.level,
            xp=user.xp,
            reputation=user.reputation,
            message_count=user.message_count,
            daily_message_count=user.daily_message_count,
            balance=balance,
            gems=gems,
        )

    # ========================================================================
    # BALANCE
    # ========================================================================

    async def get_balance(
        self,
        *,
        user_id: int,
    ) -> Decimal:
        """
        Получить баланс пользователя.
        """

        if user_id <= 0:
            raise ValueError("Invalid user_id.")

        return await self.economy.get_balance(
            user_id,
        )

    # ========================================================================
    # GEMS
    # ========================================================================

    async def get_gems(
        self,
        *,
        user_id: int,
    ) -> int:
        """
        Получить количество гемов пользователя.
        """

        if user_id <= 0:
            raise ValueError("Invalid user_id.")

        return await self.economy.get_gems(
            user_id,
        )

    # ========================================================================
    # ACTIVITY
    # ========================================================================

    async def get_message_count(
        self,
        *,
        user_id: int,
    ) -> int:
        """
        Получить общее количество сообщений.
        """

        if user_id <= 0:
            raise ValueError("Invalid user_id.")

        user = await self.users.get_by_id(
            user_id,
        )

        if user is None:
            raise ValueError(
                f"User {user_id} does not exist."
            )

        return user.message_count

    async def get_daily_message_count(
        self,
        *,
        user_id: int,
    ) -> int:
        """
        Получить количество сообщений за текущий
        расчётный период.
        """

        if user_id <= 0:
            raise ValueError("Invalid user_id.")

        user = await self.users.get_by_id(
            user_id,
        )

        if user is None:
            raise ValueError(
                f"User {user_id} does not exist."
            )

        return user.daily_message_count

    # ========================================================================
    # PROGRESSION
    # ========================================================================

    async def get_progression(
        self,
        *,
        user_id: int,
    ) -> dict[str, int]:
        """
        Получить RPG-прогрессию пользователя.
        """

        if user_id <= 0:
            raise ValueError("Invalid user_id.")

        user = await self.users.get_by_id(
            user_id,
        )

        if user is None:
            raise ValueError(
                f"User {user_id} does not exist."
            )

        return {
            "level": user.level,
            "xp": user.xp,
            "reputation": user.reputation,
        }

    # ========================================================================
    # ACTIVITY SUMMARY
    # ========================================================================

    async def get_activity_summary(
        self,
        *,
        user_id: int,
    ) -> dict[str, int]:
        """
        Получить сводку активности пользователя.
        """

        if user_id <= 0:
            raise ValueError("Invalid user_id.")

        user = await self.users.get_by_id(
            user_id,
        )

        if user is None:
            raise ValueError(
                f"User {user_id} does not exist."
            )

        return {
            "message_count": user.message_count,
            "daily_message_count": user.daily_message_count,
        }

    # ========================================================================
    # ECONOMY SUMMARY
    # ========================================================================

    async def get_economy_summary(
        self,
        *,
        user_id: int,
    ) -> dict[str, Decimal | int]:
        """
        Получить экономическую сводку пользователя.
        """

        if user_id <= 0:
            raise ValueError("Invalid user_id.")

        return {
            "balance": await self.economy.get_balance(
                user_id,
            ),
            "gems": await self.economy.get_gems(
                user_id,
            ),
        }