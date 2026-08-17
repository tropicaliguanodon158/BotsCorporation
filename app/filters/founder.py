from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config.settings import settings


class FounderFilter(BaseFilter):
    """
    Фильтр основателя бота.

    Доступ разрешён только Telegram-пользователю,
    чей ID указан в конфигурации приложения.

    Важно:

        Founder != Telegram administrator

    Основатель определяется именно по Telegram ID.

    Это означает, что даже если человек:
        - администратор чата;
        - владелец группы;
        - получил высокий игровой ранг;
        - имеет максимальный уровень модерации;

    он НЕ становится основателем автоматически.

    Founder ID задаётся в .env.
    """

    async def __call__(
        self,
        event: TelegramObject,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Проверяет Telegram ID отправителя события.
        """

        founder_id = settings.founder_id

        # Founder ID обязан быть задан.
        #
        # Если его нет, Founder Panel полностью закрыт.
        #
        # Это безопаснее, чем случайно разрешить доступ
        # кому-либо.

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
        """
        Получает Telegram ID пользователя из события.

        Поддерживаем:
            Message
            CallbackQuery

        И оставляем fallback для других Telegram events.
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