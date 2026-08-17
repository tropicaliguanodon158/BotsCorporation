from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config.settings import settings


class FounderFilter(BaseFilter):
    """
    Фильтр основателя бота.

    Founder определяется исключительно по Telegram ID,
    указанному в конфигурации.

    Founder не зависит от:
        - Telegram-роли в чате;
        - ChatAdmin;
        - AdminLevel;
        - игровых рангов;
        - permissions.
    """

    async def __call__(
        self,
        event: TelegramObject,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        founder_id = settings.FOUNDER_ID

        if founder_id is None:
            return False

        user_id = self._get_user_id(event)

        if user_id is None:
            return False

        return user_id == founder_id

    @staticmethod
    def _get_user_id(
        event: TelegramObject,
    ) -> int | None:
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
