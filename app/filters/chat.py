from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.chat import Chat


class ChatFilter(BaseFilter):
    """
    Фильтр состояния Telegram-чата.

    Используется для проверки:

        - существует ли чат в БД;
        - активирован ли бот;
        - включена ли конкретная функция.

    Примеры:

        ChatFilter()

        ChatFilter("economy_enabled")

        ChatFilter("games_enabled")

        ChatFilter("characters_enabled")

        ChatFilter("moderation_enabled")

    В личных сообщениях фильтр по умолчанию не пропускает
    событие, поскольку Chat относится именно к чатам,
    где бот работает как групповой бот.
    """

    def __init__(
        self,
        feature: str | None = None,
    ) -> None:
        self.feature = feature

    async def __call__(
        self,
        event: TelegramObject,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        session = kwargs.get("session")

        if not isinstance(session, AsyncSession):
            return False

        chat_id = self._get_chat_id(event)

        if chat_id is None:
            return False

        chat = await self._get_chat(
            session=session,
            chat_id=chat_id,
        )

        if chat is None:
            return False

        if not chat.is_active:
            return False

        # Если конкретная функция не указана,
        # достаточно того, что чат активен.

        if self.feature is None:
            return True

        return self._is_feature_enabled(
            chat=chat,
            feature=self.feature,
        )

    @staticmethod
    async def _get_chat(
        session: AsyncSession,
        chat_id: int,
    ) -> Chat | None:
        """
        Получает настройки чата из БД.
        """

        result = await session.execute(
            select(Chat).where(
                Chat.id == chat_id,
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    def _is_feature_enabled(
        chat: Chat,
        feature: str,
    ) -> bool:
        """
        Проверяет, включена ли конкретная функция.

        Используем whitelist вместо getattr(),
        чтобы случайно нельзя было обратиться
        к произвольному атрибуту модели.
        """

        allowed_features = {
            "economy_enabled",
            "moderation_enabled",
            "automod_enabled",
            "antiflood_enabled",
            "games_enabled",
            "interactions_enabled",
            "characters_enabled",
            "abilities_enabled",
            "passive_income_enabled",
            "leveling_enabled",
            "welcome_enabled",
            "logging_enabled",
        }

        if feature not in allowed_features:
            return False

        return bool(
            getattr(chat, feature)
        )

    @staticmethod
    def _get_chat_id(
        event: TelegramObject,
    ) -> int | None:
        """
        Получает Telegram ID чата из Telegram Update.
        """

        # --------------------------------------------------------------
        # Message
        # --------------------------------------------------------------

        if isinstance(event, Message):
            if event.chat is not None:
                return event.chat.id

            return None

        # --------------------------------------------------------------
        # CallbackQuery
        # --------------------------------------------------------------

        if isinstance(event, CallbackQuery):
            if event.message is not None:
                return event.message.chat.id

            return None

        # --------------------------------------------------------------
        # Fallback
        # --------------------------------------------------------------

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