from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Sequence

from app.database.models.moderation import (
    ModerationAction,
    ModerationFilter,
    UserWarning,
)
from app.database.repositories.moderation import ModerationRepository


class ModerationService:
    """
    Бизнес-логика модерации.

    Telegram API сюда не попадает.
    Service только принимает решение и фиксирует его в БД.

    Реальные ban/mute/delete выполняются handler-слоем.
    """

    ACTIONS = {
        "warn",
        "mute",
        "unmute",
        "kick",
        "ban",
        "unban",
        "delete_message",
        "restrict",
        "unrestrict",
    }

    def __init__(
        self,
        repository: ModerationRepository,
    ) -> None:
        self.repository = repository

    # ========================================================================
    # ACTIONS
    # ========================================================================

    async def record_action(
        self,
        *,
        moderator_id: int | None,
        target_user_id: int,
        chat_id: int,
        action_type: str,
        reason: str | None = None,
        duration_seconds: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ModerationAction:
        action_type = action_type.strip().lower()

        if action_type not in self.ACTIONS:
            raise ValueError(
                f"Unsupported moderation action: {action_type}"
            )

        if target_user_id == moderator_id:
            raise ValueError(
                "Moderator cannot moderate themselves."
            )

        expires_at = None

        if duration_seconds is not None:
            if duration_seconds <= 0:
                raise ValueError(
                    "duration_seconds must be greater than zero."
                )

            expires_at = (
                datetime.now()
                + timedelta(seconds=duration_seconds)
            )

        return await self.repository.create_action(
            moderator_id=moderator_id,
            target_user_id=target_user_id,
            chat_id=chat_id,
            action_type=action_type,
            reason=reason,
            duration_seconds=duration_seconds,
            expires_at=expires_at,
            metadata=metadata,
        )

    async def get_user_history(
        self,
        *,
        target_user_id: int,
        chat_id: int | None = None,
        action_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[ModerationAction]:
        return await self.repository.get_user_actions(
            target_user_id=target_user_id,
            chat_id=chat_id,
            action_type=action_type,
            limit=limit,
            offset=offset,
        )

    # ========================================================================
    # WARNINGS
    # ========================================================================

    async def warn(
        self,
        *,
        moderator_id: int | None,
        target_user_id: int,
        chat_id: int,
        reason: str | None = None,
        duration_seconds: int | None = None,
    ) -> UserWarning:
        expires_at = None

        if duration_seconds is not None:
            if duration_seconds <= 0:
                raise ValueError(
                    "Warning duration must be greater than zero."
                )

            expires_at = (
                datetime.now()
                + timedelta(seconds=duration_seconds)
            )

        warning = await self.repository.create_warning(
            user_id=target_user_id,
            chat_id=chat_id,
            moderator_id=moderator_id,
            reason=reason,
            expires_at=expires_at,
        )

        await self.repository.create_action(
            moderator_id=moderator_id,
            target_user_id=target_user_id,
            chat_id=chat_id,
            action_type="warn",
            reason=reason,
            duration_seconds=duration_seconds,
            expires_at=expires_at,
        )

        return warning

    async def get_warning_count(
        self,
        *,
        user_id: int,
        chat_id: int,
    ) -> int:
        return await self.repository.count_active_warnings(
            user_id=user_id,
            chat_id=chat_id,
            now=datetime.now(),
        )

    async def get_active_warnings(
        self,
        *,
        user_id: int,
        chat_id: int,
    ) -> Sequence[UserWarning]:
        return await self.repository.get_active_warnings(
            user_id=user_id,
            chat_id=chat_id,
            now=datetime.now(),
        )

    async def clear_warnings(
        self,
        *,
        moderator_id: int | None,
        target_user_id: int,
        chat_id: int,
        reason: str | None = None,
    ) -> int:
        count = await self.repository.deactivate_user_warnings(
            user_id=target_user_id,
            chat_id=chat_id,
        )

        if count:
            await self.repository.create_action(
                moderator_id=moderator_id,
                target_user_id=target_user_id,
                chat_id=chat_id,
                action_type="unwarn",
                reason=reason,
                metadata={
                    "deactivated_count": count,
                },
            )

        return count

    # ========================================================================
    # FILTERS
    # ========================================================================

    async def create_filter(
        self,
        *,
        chat_id: int,
        pattern: str,
        match_type: str = "contains",
        action_type: str = "delete",
        duration_seconds: int | None = None,
        reason: str | None = None,
    ) -> ModerationFilter:
        return await self.repository.create_filter(
            chat_id=chat_id,
            pattern=pattern,
            match_type=match_type,
            action_type=action_type,
            duration_seconds=duration_seconds,
            reason=reason,
        )

    async def get_active_filters(
        self,
        chat_id: int,
    ) -> Sequence[ModerationFilter]:
        return await self.repository.get_active_filters(
            chat_id=chat_id,
        )

    @staticmethod
    def _matches(
        *,
        text: str,
        moderation_filter: ModerationFilter,
    ) -> bool:
        pattern = moderation_filter.pattern

        text_lower = text.lower()
        pattern_lower = pattern.lower()

        match_type = moderation_filter.match_type

        if match_type == "exact":
            return text_lower == pattern_lower

        if match_type == "contains":
            return pattern_lower in text_lower

        if match_type == "starts_with":
            return text_lower.startswith(pattern_lower)

        if match_type == "ends_with":
            return text_lower.endswith(pattern_lower)

        if match_type == "regex":
            try:
                return re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                ) is not None
            except re.error:
                return False

        return False

    async def check_message(
        self,
        *,
        chat_id: int,
        text: str,
    ) -> list[ModerationFilter]:
        if not text.strip():
            return []

        filters = await self.repository.get_active_filters(
            chat_id=chat_id,
        )

        return [
            moderation_filter
            for moderation_filter in filters
            if self._matches(
                text=text,
                moderation_filter=moderation_filter,
            )
        ]

    # ========================================================================
    # MAINTENANCE
    # ========================================================================

    async def cleanup_expired(
        self,
    ) -> dict[str, int]:
        now = datetime.now()

        warnings = await self.repository.deactivate_expired_warnings(
            now=now,
        )

        actions = await self.repository.get_expired_actions(
            now=now,
        )

        return {
            "warnings": warnings,
            "actions": len(actions),
        }