```python
from __future__ import annotations

from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User


class UserRepository:
    """
    Репозиторий пользователей Telegram.

    Только работа с таблицей users.
    Бизнес-логика находится в service-слое.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # ========================================================================
    # GET
    # ========================================================================

    async def get_by_id(
        self,
        user_id: int,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_id_for_update(
        self,
        user_id: int,
    ) -> User | None:
        """
        Получить пользователя для конкурентной операции.

        PostgreSQL:
            используется SELECT ... FOR UPDATE.

        SQLite:
            SELECT ... FOR UPDATE не поддерживается,
            поэтому защита конкурентных операций должна
            дополнительно обеспечиваться атомарными
            операциями и ограничениями БД.

        Метод оставлен единым для обеих СУБД.
        """

        query = select(User).where(
            User.id == user_id,
        )

        bind = self.session.get_bind()

        if bind.dialect.name != "sqlite":
            query = query.with_for_update()

        result = await self.session.execute(
            query
        )

        return result.scalar_one_or_none()

    async def get_many(
        self,
        user_ids: Sequence[int],
    ) -> list[User]:
        if not user_ids:
            return []

        result = await self.session.execute(
            select(User).where(
                User.id.in_(user_ids),
            )
        )

        return list(
            result.scalars().all()
        )

    async def exists(
        self,
        user_id: int,
    ) -> bool:
        result = await self.session.execute(
            select(User.id).where(
                User.id == user_id,
            )
        )

        return (
            result.scalar_one_or_none()
            is not None
        )

    # ========================================================================
    # CREATE
    # ========================================================================

    async def create(
        self,
        user_id: int,
        first_name: str,
        last_name: str | None = None,
        username: str | None = None,
    ) -> User:
        if user_id <= 0:
            raise ValueError(
                "Invalid Telegram user_id."
            )

        if not first_name:
            raise ValueError(
                "Telegram first_name cannot be empty."
            )

        user = User(
            id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )

        self.session.add(user)

        await self.session.flush()

        return user

    # ========================================================================
    # GET OR CREATE
    # ========================================================================

    async def get_or_create(
        self,
        user_id: int,
        first_name: str,
        last_name: str | None = None,
        username: str | None = None,
    ) -> tuple[User, bool]:
        """
        Получает пользователя или создаёт его.

        users.id является PRIMARY KEY и дополнительно
        защищает от существования двух одинаковых
        Telegram пользователей.
        """

        user = await self.get_by_id(
            user_id
        )

        if user is not None:
            return user, False

        user = await self.create(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )

        return user, True

    # ========================================================================
    # UPDATE
    # ========================================================================

    async def update_profile(
        self,
        user_id: int,
        first_name: str,
        last_name: str | None,
        username: str | None,
    ) -> User | None:
        """
        Полностью синхронизирует профиль
        с актуальными данными Telegram.
        """

        if not first_name:
            raise ValueError(
                "Telegram first_name cannot be empty."
            )

        user = await self.get_by_id(
            user_id
        )

        if user is None:
            return None

        user.first_name = first_name
        user.last_name = last_name
        user.username = username

        await self.session.flush()

        return user

    async def set_active(
        self,
        user_id: int,
        is_active: bool,
    ) -> bool:
        result = await self.session.execute(
            update(User)
            .where(
                User.id == user_id
            )
            .values(
                is_active=is_active
            )
        )

        return result.rowcount > 0

    # ========================================================================
    # XP
    # ========================================================================

    async def add_xp(
        self,
        user_id: int,
        amount: int,
    ) -> User | None:
        if amount == 0:
            return await self.get_by_id(
                user_id
            )

        user = await self.get_by_id(
            user_id
        )

        if user is None:
            return None

        user.xp += amount

        await self.session.flush()

        return user

    async def set_xp(
        self,
        user_id: int,
        amount: int,
    ) -> User | None:
        user = await self.get_by_id(
            user_id
        )

        if user is None:
            return None

        user.xp = max(0, amount)

        await self.session.flush()

        return user

    # ========================================================================
    # LEVEL
    # ========================================================================

    async def set_level(
        self,
        user_id: int,
        level: int,
    ) -> User | None:
        user = await self.get_by_id(
            user_id
        )

        if user is None:
            return None

        user.level = max(1, level)

        await self.session.flush()

        return user

    # ========================================================================
    # REPUTATION
    # ========================================================================

    async def add_reputation(
        self,
        user_id: int,
        amount: int,
    ) -> User | None:
        user = await self.get_by_id(
            user_id
        )

        if user is None:
            return None

        user.reputation += amount

        await self.session.flush()

        return user

    async def set_reputation(
        self,
        user_id: int,
        amount: int,
    ) -> User | None:
        user = await self.get_by_id(
            user_id
        )

        if user is None:
            return None

        user.reputation = amount

        await self.session.flush()

        return user

    # ========================================================================
    # MESSAGE ACTIVITY
    # ========================================================================

    async def increment_message_count(
        self,
        user_id: int,
        amount: int = 1,
    ) -> User | None:
        if amount <= 0:
            return await self.get_by_id(
                user_id
            )

        user = await self.get_by_id(
            user_id
        )

        if user is None:
            return None

        user.message_count += amount

        await self.session.flush()

        return user

    async def increment_daily_message_count(
        self,
        user_id: int,
        amount: int = 1,
    ) -> User | None:
        if amount <= 0:
            return await self.get_by_id(
                user_id
            )

        user = await self.get_by_id(
            user_id
        )

        if user is None:
            return None

        user.daily_message_count += amount

        await self.session.flush()

        return user

    async def reset_daily_message_count(
        self,
        user_id: int,
    ) -> User | None:
        user = await self.get_by_id(
            user_id
        )

        if user is None:
            return None

        user.daily_message_count = 0

        await self.session.flush()

        return user

    # ========================================================================
    # DELETE / DEACTIVATE
    # ========================================================================

    async def deactivate(
        self,
        user_id: int,
    ) -> bool:
        return await self.set_active(
            user_id,
            False,
        )
```
