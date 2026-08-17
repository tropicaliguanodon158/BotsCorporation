from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class AntiFloodMiddleware(BaseMiddleware):
    """
    Тихий антифлуд.

    Middleware отслеживает частоту сообщений пользователей
    отдельно для каждого чата.

    Важные принципы:

    1. Никаких сообщений от бота при обнаружении флуда.
    2. Не блокируем пользователя Telegram автоматически.
    3. Просто прекращаем дальнейшую обработку слишком частых
       сообщений.
    4. Для каждого пользователя и чата используется отдельная
       история сообщений.
    5. Старые записи автоматически удаляются из памяти.

    Это middleware отвечает именно за технический антифлуд.

    Реальная модерация:
        mute
        warn
        ban
        delete

    будет находиться в moderation service.
    """

    def __init__(
        self,
        max_messages: int = 5,
        interval_seconds: float = 3.0,
        cleanup_interval_seconds: float = 60.0,
    ) -> None:
        """
        Args:
            max_messages:
                Максимальное количество сообщений.

            interval_seconds:
                За какой промежуток времени считаются сообщения.

            cleanup_interval_seconds:
                Как часто очищать устаревшие записи.
        """

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
        self.cleanup_interval_seconds = (
            cleanup_interval_seconds
        )

        # ------------------------------------------------------------------
        # Message history
        # ------------------------------------------------------------------
        #
        # Структура:
        #
        # {
        #     chat_id: {
        #         user_id: deque([timestamp, timestamp, ...])
        #     }
        # }
        #
        # deque выбран специально, потому что нам нужно быстро
        # удалять самые старые записи.

        self._messages: dict[
            int,
            dict[int, deque[float]],
        ] = defaultdict(
            lambda: defaultdict(deque)
        )

        # Последний момент очистки памяти.

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
        Проверяет сообщение на флуд.

        Если пользователь не превысил лимит —
        передаём событие дальше.

        Если превысил —
        молча прекращаем обработку.
        """

        # --------------------------------------------------------------
        # Проверяем, является ли событие сообщением
        # --------------------------------------------------------------

        if not isinstance(event, Message):
            return await handler(event, data)

        # --------------------------------------------------------------
        # Получаем необходимые данные
        # --------------------------------------------------------------

        if event.from_user is None:
            return await handler(event, data)

        if event.chat is None:
            return await handler(event, data)

        user_id = event.from_user.id
        chat_id = event.chat.id

        # --------------------------------------------------------------
        # Пропускаем личные сообщения
        # --------------------------------------------------------------
        #
        # Антифлуд нужен прежде всего для групп.
        #
        # В ЛС основателю и пользователям он нам мешать не должен.

        if event.chat.type == "private":
            return await handler(event, data)

        # --------------------------------------------------------------
        # Очистка старых данных
        # --------------------------------------------------------------

        now = time.monotonic()

        if (
            now - self._last_cleanup
            >= self.cleanup_interval_seconds
        ):
            self._cleanup(now)
            self._last_cleanup = now

        # --------------------------------------------------------------
        # Получаем историю пользователя
        # --------------------------------------------------------------

        user_messages = self._messages[chat_id][user_id]

        # --------------------------------------------------------------
        # Удаляем сообщения, вышедшие за временное окно
        # --------------------------------------------------------------

        cutoff = now - self.interval_seconds

        while user_messages and user_messages[0] <= cutoff:
            user_messages.popleft()

        # --------------------------------------------------------------
        # Проверяем лимит
        # --------------------------------------------------------------

        if len(user_messages) >= self.max_messages:
            # Сообщение считается флудом.
            #
            # Ничего пользователю не отправляем.
            # Никаких исключений.
            #
            # Просто не передаём событие дальше.

            return None

        # --------------------------------------------------------------
        # Регистрируем сообщение
        # --------------------------------------------------------------

        user_messages.append(now)

        # --------------------------------------------------------------
        # Передаём управление следующему middleware / handler
        # --------------------------------------------------------------

        return await handler(event, data)

    def _cleanup(self, now: float) -> None:
        """
        Удаляет устаревшие записи из памяти.

        Это необходимо, чтобы словари не росли бесконечно
        при большом количестве пользователей и чатов.
        """

        cutoff = now - self.interval_seconds

        empty_users: list[
            tuple[int, int]
        ] = []

        for chat_id, users in self._messages.items():
            for user_id, timestamps in users.items():

                while timestamps and timestamps[0] <= cutoff:
                    timestamps.popleft()

                if not timestamps:
                    empty_users.append(
                        (chat_id, user_id)
                    )

        # Удаляем пустые записи пользователей.

        for chat_id, user_id in empty_users:
            users = self._messages.get(chat_id)

            if users is None:
                continue

            users.pop(user_id, None)

        # Удаляем пустые чаты.

        empty_chats = [
            chat_id
            for chat_id, users in self._messages.items()
            if not users
        ]

        for chat_id in empty_chats:
            self._messages.pop(chat_id, None)

    def reset_user(
        self,
        chat_id: int,
        user_id: int,
    ) -> None:
        """
        Сбрасывает антифлуд для конкретного пользователя.

        Может пригодиться после ручного вмешательства
        администратора.
        """

        users = self._messages.get(chat_id)

        if users is None:
            return

        users.pop(user_id, None)

        if not users:
            self._messages.pop(chat_id, None)

    def reset_chat(
        self,
        chat_id: int,
    ) -> None:
        """
        Полностью сбрасывает антифлуд конкретного чата.
        """

        self._messages.pop(chat_id, None)

    def reset_all(self) -> None:
        """
        Полностью очищает состояние антифлуда.
        """

        self._messages.clear()