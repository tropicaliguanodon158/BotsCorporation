from __future__ import annotations

import json
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.chat import Chat


T = TypeVar("T")


class SettingsRepository:
    """
    Репозиторий настроек Telegram-чатов.

    Основные настройки находятся в модели Chat.
    Дополнительные динамические настройки хранятся
    в Chat.settings_json.

    Все изменения выполняются в текущей SQLAlchemy session.
    commit/rollback выполняется внешним middleware.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # ========================================================================
    # CHAT
    # ========================================================================

    async def get_chat(
        self,
        chat_id: int,
    ) -> Chat | None:
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
        if chat_id == 0:
            raise ValueError(
                "Invalid chat_id."
            )

        chat = await self.get_chat(
            chat_id,
        )

        if chat is not None:
            changed = False

            if (
                title is not None
                and chat.title != title
            ):
                chat.title = title
                changed = True

            if (
                username is not None
                and chat.username != username
            ):
                chat.username = username
                changed = True

            if chat.chat_type != chat_type:
                chat.chat_type = chat_type
                changed = True

            if changed:
                await self.session.flush()

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
    # JSON
    # ========================================================================

    @staticmethod
    def _load_settings(
        chat: Chat,
    ) -> dict[str, Any]:
        raw = chat.settings_json

        if not raw:
            return {}

        try:
            data = json.loads(raw)
        except (
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ):
            return {}

        if not isinstance(data, dict):
            return {}

        return data

    @staticmethod
    def _save_settings(
        chat: Chat,
        values: dict[str, Any],
    ) -> None:
        chat.settings_json = json.dumps(
            values,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        )

    # ========================================================================
    # GET
    # ========================================================================

    async def get(
        self,
        *,
        chat_id: int,
        key: str,
        default: T | None = None,
    ) -> T | None:
        key = key.strip()

        if not key:
            return default

        chat = await self.get_chat(
            chat_id,
        )

        if chat is None:
            return default

        values = self._load_settings(
            chat,
        )

        return values.get(
            key,
            default,
        )

    async def get_all(
        self,
        *,
        chat_id: int,
    ) -> dict[str, Any]:
        chat = await self.get_chat(
            chat_id,
        )

        if chat is None:
            return {}

        return self._load_settings(
            chat,
        )

    async def get_by_prefix(
        self,
        *,
        chat_id: int,
        prefix: str,
    ) -> dict[str, Any]:
        values = await self.get_all(
            chat_id=chat_id,
        )

        prefix = prefix.strip()

        if not prefix:
            return values

        return {
            key: value
            for key, value in values.items()
            if key.startswith(prefix)
        }

    # ========================================================================
    # SET
    # ========================================================================

    async def set(
        self,
        *,
        chat_id: int,
        key: str,
        value: Any,
    ) -> Any:
        key = key.strip()

        if not key:
            raise ValueError(
                "Setting key cannot be empty."
            )

        chat = await self.get_chat(
            chat_id,
        )

        if chat is None:
            raise ValueError(
                f"Chat {chat_id} does not exist."
            )

        values = self._load_settings(
            chat,
        )

        values[key] = value

        self._save_settings(
            chat,
            values,
        )

        await self.session.flush()

        return value

    async def set_many(
        self,
        *,
        chat_id: int,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        chat = await self.get_chat(
            chat_id,
        )

        if chat is None:
            raise ValueError(
                f"Chat {chat_id} does not exist."
            )

        current = self._load_settings(
            chat,
        )

        for key, value in values.items():
            normalized_key = key.strip()

            if not normalized_key:
                raise ValueError(
                    "Setting key cannot be empty."
                )

            current[normalized_key] = value

        self._save_settings(
            chat,
            current,
        )

        await self.session.flush()

        return current

    # ========================================================================
    # DELETE
    # ========================================================================

    async def delete(
        self,
        *,
        chat_id: int,
        key: str,
    ) -> bool:
        key = key.strip()

        if not key:
            return False

        chat = await self.get_chat(
            chat_id,
        )

        if chat is None:
            return False

        values = self._load_settings(
            chat,
        )

        if key not in values:
            return False

        del values[key]

        self._save_settings(
            chat,
            values,
        )

        await self.session.flush()

        return True

    async def delete_by_prefix(
        self,
        *,
        chat_id: int,
        prefix: str,
    ) -> int:
        chat = await self.get_chat(
            chat_id,
        )

        if chat is None:
            return 0

        prefix = prefix.strip()

        if not prefix:
            return 0

        values = self._load_settings(
            chat,
        )

        keys = [
            key
            for key in values
            if key.startswith(prefix)
        ]

        if not keys:
            return 0

        for key in keys:
            del values[key]

        self._save_settings(
            chat,
            values,
        )

        await self.session.flush()

        return len(keys)

    # ========================================================================
    # RESET
    # ========================================================================

    async def reset_dynamic_settings(
        self,
        *,
        chat_id: int,
    ) -> bool:
        chat = await self.get_chat(
            chat_id,
        )

        if chat is None:
            return False

        chat.settings_json = "{}"

        await self.session.flush()

        return True
