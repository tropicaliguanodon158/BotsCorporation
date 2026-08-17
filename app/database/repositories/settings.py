from __future__ import annotations

import json
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.chat import Chat


T = TypeVar("T")


class SettingsRepository:
    """
    Repository для настроек Telegram-чатов.

    Важные и часто используемые настройки находятся
    непосредственно в модели Chat.

    Дополнительные динамические настройки хранятся
    в Chat.settings_json.

    Это позволяет Founder Panel добавлять новые
    параметры без изменения структуры БД.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ========================================================================
    # CHAT
    # ========================================================================

    async def get_chat(
        self,
        chat_id: int,
    ) -> Chat | None:
        """
        Получить чат по Telegram ID.
        """

        result = await self.session.execute(
            select(Chat).where(
                Chat.id == chat_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_or_create_chat(
        self,
        *,
        chat_id: int,
        title: str | None = None,
        username: str | None = None,
        chat_type: str = "group",
    ) -> Chat:
        """
        Получить существующий чат или создать его.
        """

        chat = await self.get_chat(chat_id)

        if chat is not None:
            return chat

        chat = Chat(
            id=chat_id,
            title=title,
            username=username,
            chat_type=chat_type,
        )

        self.session.add(chat)

        await self.session.flush()

        return chat

    # ========================================================================
    # JSON SETTINGS
    # ========================================================================

    @staticmethod
    def _load_settings(
        chat: Chat,
    ) -> dict[str, Any]:
        """
        Загрузить settings_json.

        Если JSON отсутствует или повреждён,
        возвращается пустой словарь.
        """

        if not chat.settings_json:
            return {}

        try:
            data = json.loads(chat.settings_json)

            if isinstance(data, dict):
                return data

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            pass

        return {}

    @staticmethod
    def _save_settings(
        chat: Chat,
        settings: dict[str, Any],
    ) -> None:
        """
        Сохранить словарь настроек в JSON.
        """

        chat.settings_json = json.dumps(
            settings,
            ensure_ascii=False,
        )

    # ========================================================================
    # DYNAMIC GET
    # ========================================================================

    async def get(
        self,
        *,
        chat_id: int,
        key: str,
        default: T | None = None,
    ) -> T | None:
        """
        Получить динамическую настройку.

        Пример:

            economy.hourly_reward

        Если параметр отсутствует, возвращается default.
        """

        chat = await self.get_chat(chat_id)

        if chat is None:
            return default

        settings = self._load_settings(chat)

        value = settings.get(key, default)

        return value

    # ========================================================================
    # DYNAMIC SET
    # ========================================================================

    async def set(
        self,
        *,
        chat_id: int,
        key: str,
        value: Any,
    ) -> Any:
        """
        Создать или изменить динамическую настройку.

        Пример:

            await repository.set(
                chat_id=123,
                key="games.duel_price",
                value=100,
            )
        """

        if not key or not key.strip():
            raise ValueError(
                "Setting key cannot be empty."
            )

        chat = await self.get_chat(chat_id)

        if chat is None:
            raise ValueError(
                f"Chat {chat_id} does not exist."
            )

        key = key.strip()

        settings = self._load_settings(chat)

        settings[key] = value

        self._save_settings(
            chat,
            settings,
        )

        await self.session.flush()

        return value

    # ========================================================================
    # DYNAMIC DELETE
    # ========================================================================

    async def delete(
        self,
        *,
        chat_id: int,
        key: str,
    ) -> bool:
        """
        Удалить динамическую настройку.
        """

        chat = await self.get_chat(chat_id)

        if chat is None:
            return False

        settings = self._load_settings(chat)

        if key not in settings:
            return False

        del settings[key]

        self._save_settings(
            chat,
            settings,
        )

        await self.session.flush()

        return True

    # ========================================================================
    # GET ALL
    # ========================================================================

    async def get_all(
        self,
        *,
        chat_id: int,
    ) -> dict[str, Any]:
        """
        Получить все динамические настройки чата.
        """

        chat = await self.get_chat(chat_id)

        if chat is None:
            return {}

        return self._load_settings(chat)

    # ========================================================================
    # GET BY PREFIX
    # ========================================================================

    async def get_by_prefix(
        self,
        *,
        chat_id: int,
        prefix: str,
    ) -> dict[str, Any]:
        """
        Получить настройки по префиксу.

        Например:

            economy.

        вернёт:

            economy.hourly_reward
            economy.daily_reward
            economy.required_messages
        """

        settings = await self.get_all(chat_id)

        return {
            key: value
            for key, value in settings.items()
            if key.startswith(prefix)
        }

    # ========================================================================
    # SET MANY
    # ========================================================================

    async def set_many(
        self,
        *,
        chat_id: int,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Изменить несколько динамических настроек.
        """

        chat = await self.get_chat(chat_id)

        if chat is None:
            raise ValueError(
                f"Chat {chat_id} does not exist."
            )

        settings = self._load_settings(chat)

        for key, value in values.items():

            if not key or not key.strip():
                raise ValueError(
                    "Setting key cannot be empty."
                )

            settings[key.strip()] = value

        self._save_settings(
            chat,
            settings,
        )

        await self.session.flush()

        return settings

    # ========================================================================
    # DELETE BY PREFIX
    # ========================================================================

    async def delete_by_prefix(
        self,
        *,
        chat_id: int,
        prefix: str,
    ) -> int:
        """
        Удалить все динамические настройки,
        начинающиеся с указанного префикса.

        Возвращает количество удалённых параметров.
        """

        chat = await self.get_chat(chat_id)

        if chat is None:
            return 0

        settings = self._load_settings(chat)

        keys_to_delete = [
            key
            for key in settings
            if key.startswith(prefix)
        ]

        for key in keys_to_delete:
            del settings[key]

        if keys_to_delete:
            self._save_settings(
                chat,
                settings,
            )

            await self.session.flush()

        return len(keys_to_delete)

    # ========================================================================
    # RESET
    # ========================================================================

    async def reset_dynamic_settings(
        self,
        *,
        chat_id: int,
    ) -> bool:
        """
        Полностью очистить settings_json.

        Важно:
        основные поля Chat при этом НЕ изменяются.
        """

        chat = await self.get_chat(chat_id)

        if chat is None:
            return False

        chat.settings_json = "{}"

        await self.session.flush()

        return True