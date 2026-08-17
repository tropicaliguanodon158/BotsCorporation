from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.admin import ChatAdmin, AdminLevel


class AdminFilter(BaseFilter):
    """
    Проверка административного уровня пользователя
    в конкретном чате.

    required_level:
        1 = минимальный административный доступ
        2 = выше
        ...
        5 = максимальный стандартный уровень

    Founder не проверяется здесь.
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
        session = kwargs.get("session")

        if not isinstance(
            session,
            AsyncSession,
        ):
            return False

        user_id = self._get_user_id(event)

        if user_id is None:
            return False

        chat_id = self._get_chat_id(event)

        if chat_id is None:
            return False

        result = await session.execute(
            select(ChatAdmin)
            .join(
                AdminLevel,
                AdminLevel.id
                == ChatAdmin.admin_level_id,
            )
            .where(
                ChatAdmin.user_id == user_id,
                ChatAdmin.chat_id == chat_id,
                ChatAdmin.is_active.is_(True),
                AdminLevel.is_active.is_(True),
                AdminLevel.level
                >= self.required_level,
            )
            .limit(1)
        )

        return (
            result.scalar_one_or_none()
            is not None
        )

    @staticmethod
    def _get_user_id(
        event: TelegramObject,
    ) -> int | None:
        if isinstance(event, Message):
            return (
                event.from_user.id
                if event.from_user is not None
                else None
            )

        if isinstance(event, CallbackQuery):
            return (
                event.from_user.id
                if event.from_user is not None
                else None
            )

        telegram_user = getattr(
            event,
            "from_user",
            None,
        )

        return getattr(
            telegram_user,
            "id",
            None,
        )

    @staticmethod
    def _get_chat_id(
        event: TelegramObject,
    ) -> int | None:
        if isinstance(event, Message):
            if event.chat is not None:
                return event.chat.id

            return None

        if isinstance(event, CallbackQuery):
            message = event.message

            if message is not None:
                chat = getattr(
                    message,
                    "chat",
                    None,
                )

                if chat is not None:
                    return chat.id

            return None

        chat = getattr(
            event,
            "chat",
            None,
        )

        if chat is not None:
            return getattr(
                chat,
                "id",
                None,
            )

        return None
