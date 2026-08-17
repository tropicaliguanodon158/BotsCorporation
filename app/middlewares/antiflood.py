from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class AntiFloodMiddleware(BaseMiddleware):
    """
    Тихий технический антифлуд.

    Работает в рамках одного процесса бота.

    Правила:

    - действует только в групповых/супергрупповых чатах;
    - личные сообщения не ограничиваются;
    - бот ничего не отправляет при обнаружении флуда;
    - Telegram ban/mute здесь не выполняется;
    - сообщение, попавшее под flood-limit, полностью прекращает
      дальнейшую обработку update;
    - состояние хранится только в памяти процесса.
    """

    def __init__(
        self,
        max_messages: int = 5,
        interval_seconds: float = 3.0,
        cleanup_interval_seconds: float = 60.0,
    ) -> None:
        if max_messages <= 0:
            raise ValueError(
                "max_messages должен быть больше 0."
            )

        if interval_seconds <= 0:
            raise ValueError(
                "interval_seconds должен быть больше 0."
            )

        if cleanup_interval_seconds <= 0:
            raise ValueError(
                "cleanup_interval_seconds должен быть больше 0."
            )

        self.max_messages = max_messages
        self.interval_seconds = interval_seconds
        self.cleanup_interval_seconds = cleanup_interval_seconds

        self._messages: dict[
            int,
            dict[int, deque[float]],
        ] = defaultdict(
            lambda: defaultdict(deque)
        )

        self._last_cleanup = time.monotonic()

    async def __call__(
        self,
        handler: Callable[
            [TelegramObject, dict[str, Any]],
            Awaitable[Any],
        ],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Проверить update на флуд.

        Если update не является Message — пропускаем.

        Если это личное сообщение — пропускаем.

        Если пользователь превысил лимит —
        полностью прекращаем дальнейшую обработку.
        """

        if not isinstance(event, Message):
            return await handler(event, data)

        if event.from_user is None:
            return await handler(event, data)

        if event.chat is None:
            return await handler(event, data)

        # Личные сообщения не ограничиваем.
        if event.chat.type == "private":
            return await handler(event, data)

        user_id = event.from_user.id
        chat_id = event.chat.id

        now = time.monotonic()

        # Периодическая очистка общей структуры.
        if (
            now - self._last_cleanup
            >= self.cleanup_interval_seconds
        ):
            self._cleanup(now)
            self._last_cleanup = now

        user_messages = self._messages[chat_id][user_id]

        cutoff = now - self.interval_seconds

        # Удаляем timestamps, вышедшие из окна.
        while (
            user_messages
            and user_messages[0] <= cutoff
        ):
            user_messages.popleft()

        # ---------------------------------------------------------------------
        # FLOOD
        # ---------------------------------------------------------------------

        if len(user_messages) >= self.max_messages:
            # Ничего не отправляем пользователю.
            #
            # Главное:
            # handler НЕ вызывается.
            #
            # Поскольку middleware установлен на update.outer_middleware,
            # UserMiddleware также не будет вызван.
            return None

        # Сообщение прошло проверку.
        user_messages.append(now)

        return await handler(event, data)

    def _cleanup(
        self,
        now: float,
    ) -> None:
        """
        Удалить устаревшие timestamps и пустые структуры.
        """

        cutoff = now - self.interval_seconds

        empty_users: list[
            tuple[int, int]
        ] = []

        for chat_id, users in self._messages.items():
            for user_id, timestamps in users.items():

                while (
                    timestamps
                    and timestamps[0] <= cutoff
                ):
                    timestamps.popleft()

                if not timestamps:
                    empty_users.append(
                        (chat_id, user_id)
                    )

        for chat_id, user_id in empty_users:
            users = self._messages.get(chat_id)

            if users is None:
                continue

            users.pop(user_id, None)

        empty_chats = [
            chat_id
            for chat_id, users in self._messages.items()
            if not users
        ]

        for chat_id in empty_chats:
            self._messages.pop(
                chat_id,
                None,
            )

    def reset_user(
        self,
        chat_id: int,
        user_id: int,
    ) -> None:
        """
        Сбросить flood-history конкретного пользователя.
        """

        users = self._messages.get(chat_id)

        if users is None:
            return

        users.pop(
            user_id,
            None,
        )

        if not users:
            self._messages.pop(
                chat_id,
                None,
            )

    def reset_chat(
        self,
        chat_id: int,
    ) -> None:
        """
        Сбросить flood-history конкретного чата.
        """

        self._messages.pop(
            chat_id,
            None,
        )

    def reset_all(self) -> None:
        """
        Полностью очистить состояние антифлуда.
        """

        self._messages.clear()