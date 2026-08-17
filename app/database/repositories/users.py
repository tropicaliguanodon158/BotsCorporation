from __future__ import annotations

from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User


# ============================================================================
# USER REPOSITORY
# ============================================================================


class UserRepository:
    """
    Репозиторий пользователей Telegram.

    Здесь находится только работа с таблицей users.

    Бизнес-логика экономики, уровней, персонажей и модерации
    здесь находиться не должна.
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
        """
        Получает пользователя по Telegram ID.
        """

        result = await self.session.execute(
            select(User).where(
                User.id == user_id
            )
        )

        return result.scalar_one_or_none()

    async def get_many(
        self,
        user_ids: Sequence[int],
    ) -> list[User]:
        """
        Получает нескольких пользователей по ID.
        """

        if not user_ids:
            return []

        result = await self.session.execute(
            select(User).where(
                User.id.in_(user_ids)
            )
        )

        return list(result.scalars().all())

    async def exists(
        self,
        user_id: int,
    ) -> bool:
        """
        Проверяет существование пользователя.
        """

        result = await self.session.execute(
            select(User.id).where(
                User.id == user_id
            )
        )

        return result.scalar_one_or_none() is not None

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
        """
        Создаёт нового пользователя.

        Репозиторий НЕ делает commit.
        Commit контролируется уровнем выше.
        """

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

        Возвращает:

            (user, created)

        Например:

            user, created = await repo.get_or_create(...)

        created == True
            пользователь был создан.

        created == False
            пользователь уже существовал.
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
        first_name: str | None = None,
        last_name: str | None = None,
        username: str | None = None,
    ) -> User | None:
        """
        Обновляет Telegram-данные пользователя.

        None означает:
        соответствующее поле не изменять.
        """

        user = await self.get_by_id(
            user_id
        )

        if user is None:
            return None

        if first_name is not None:
            user.first_name = first_name

        if last_name is not None:
            user.last_name = last_name

        if username is not None:
            user.username = username

        await self.session.flush()

        return user

    async def set_active(
        self,
        user_id: int,
        is_active: bool,
    ) -> bool:
        """
        Включает или отключает пользователя.
        """

        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=is_active)
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
        """
        Добавляет XP пользователю.

        Само определение нового уровня будет
        происходить в service-слое.
        """

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
        """
        Устанавливает XP напрямую.

        Нужен Founder Panel и административные операции.
        """

        user = await self.get_by_id(
            user_id
        )

        if user is None:
            return None

        user.xp = max(
            0,
            amount,
        )

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
        """
        Устанавливает уровень пользователя.
        """

        user = await self.get_by_id(
            user_id
        )

        if user is None:
            return None

        user.level = max(
            1,
            level,
        )

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
        """
        Изменяет репутацию пользователя.

        Репутация может быть как положительной,
        так и отрицательной.
        """

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
        """
        Устанавливает репутацию напрямую.
        """

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
        """
        Увеличивает общее количество сообщений.
        """

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
        """
        Увеличивает количество сообщений за текущий
        расчётный день.

        Сброс суточного значения выполняется service-слоем,
        потому что он знает timezone конкретного чата.
        """

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
        """
        Сбрасывает дневной счётчик сообщений.
        """

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
        """
        Деактивирует пользователя.

        Мы не удаляем Telegram-пользователя физически,
        поскольку на него могут ссылаться:

            transactions
            games
            moderation actions
            inventory
            character
            achievements
            etc.
        """

        return await self.set_active(
            user_id,
            False,
        )