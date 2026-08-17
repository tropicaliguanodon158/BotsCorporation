from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.admin import Admin


class AdminFilter(BaseFilter):
    """
    Фильтр внутреннего администратора бота.

    Уровень администратора хранится в БД, а не определяется
    Telegram-ролью.

    Пример:

        level = 1 -> Стажёр
        level = 2 -> Модератор
        level = 3 -> Старший модератор
        level = 4 -> Верховный модератор
        level = 5 -> Главный администратор

    Названия и возможности уровней в дальнейшем будут
    полностью настраиваться через Founder Panel.

    Founder сюда не относится:
        Founder имеет отдельный FounderFilter.
    """

    def __init__(
        self,
        required_level: int = 1,
    ) -> None:
        if required_level < 1:
            raise ValueError(
                "required_level должен быть больше 0."
            )

        self.required_level = required_level

    async def __call__(
        self,
        event: TelegramObject,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Проверяет, обладает ли пользователь необходимым
        внутренним административным уровнем.
        """

        session = kwargs.get("session")

        if not isinstance(session, AsyncSession):
            return False

        user_id = self._get_user_id(event)

        if user_id is None:
            return False

        admin = await self._get_admin(
            session=session,
            user_id=user_id,
        )

        if admin is None:
            return False

        if not admin.is_active:
            return False

        return admin.level >= self.required_level

    @staticmethod
    async def _get_admin(
        session: AsyncSession,
        user_id: int,
    ) -> Admin | None:
        """
        Получает административную запись пользователя.
        """

        result = await session.execute(
            select(Admin).where(
                Admin.user_id == user_id,
                Admin.is_active.is_(True),
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    def _get_user_id(
        event: TelegramObject,
    ) -> int | None:
        """
        Получает Telegram ID пользователя из события.
        """

        if isinstance(event, Message):
            if event.from_user is not None:
                return event.from_user.id

            return None

        if isinstance(event, CallbackQuery):
            if event.from_user is not None:
                return event.from_user.id

            return None

        telegram_user = getattr(
            event,
            "from_user",
            None,
        )

        if telegram_user is None:
            return None

        return getattr(
            telegram_user,
            "id",
            None,
        )