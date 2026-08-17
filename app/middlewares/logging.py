from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.utils.logger import logger


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware технического логирования Telegram-событий.

    Логирует:

        - тип события;
        - пользователя;
        - чат;
        - callback;
        - время обработки;
        - исключения.

    Не логирует полный текст сообщений пользователей.
    """

    async def __call__(
        self,
        handler: Callable[
            [TelegramObject, dict[str, Any]],
            Awaitable[Any],
        ],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        started_at = time.perf_counter()

        event_name = type(event).__name__

        user_id = self._get_user_id(event)
        chat_id = self._get_chat_id(event)

        try:
            result = await handler(event, data)

            elapsed = (
                time.perf_counter() - started_at
            )

            logger.debug(
                "Telegram update processed | "
                "event=%s | "
                "user_id=%s | "
                "chat_id=%s | "
                "duration=%.4fs",
                event_name,
                user_id,
                chat_id,
                elapsed,
            )

            return result

        except Exception:
            elapsed = (
                time.perf_counter() - started_at
            )

            logger.exception(
                "Telegram update failed | "
                "event=%s | "
                "user_id=%s | "
                "chat_id=%s | "
                "duration=%.4fs",
                event_name,
                user_id,
                chat_id,
                elapsed,
            )

            raise

    @staticmethod
    def _get_user_id(
        event: TelegramObject,
    ) -> int | None:
        """
        Возвращает Telegram ID пользователя,
        если он присутствует в событии.
        """

        if isinstance(event, Message):
            if event.from_user is not None:
                return event.from_user.id

        if isinstance(event, CallbackQuery):
            if event.from_user is not None:
                return event.from_user.id

        telegram_user = getattr(
            event,
            "from_user",
            None,
        )

        if telegram_user is not None:
            return getattr(
                telegram_user,
                "id",
                None,
            )

        return None

    @staticmethod
    def _get_chat_id(
        event: TelegramObject,
    ) -> int | None:
        """
        Возвращает Telegram ID чата,
        если он присутствует в событии.
        """

        if isinstance(event, Message):
            if event.chat is not None:
                return event.chat.id

        if isinstance(event, CallbackQuery):
            if event.message is not None:
                return event.message.chat.id

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