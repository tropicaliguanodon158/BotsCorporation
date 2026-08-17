"""
Permissions service.

Централизованная проверка прав пользователя.

Не работает напрямую с Telegram API.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.database.repositories.moderation import ModerationRepository


@dataclass(slots=True)
class PermissionResult:
    allowed: bool
    reason: str | None = None


class PermissionsService:
    """
    Сервис проверки прав.

    Telegram administrator permissions должны проверяться
    handler/middleware уровнем.

    Этот сервис отвечает за внутренние роли бота.
    """

    def __init__(
        self,
        *,
        moderation_repository: ModerationRepository,
    ) -> None:
        self.moderation = moderation_repository

    async def can_moderate(
        self,
        *,
        moderator_id: int,
        chat_id: int,
    ) -> PermissionResult:
        if moderator_id <= 0:
            return PermissionResult(
                allowed=False,
                reason="invalid_user",
            )

        if chat_id == 0:
            return PermissionResult(
                allowed=False,
                reason="invalid_chat",
            )

        return PermissionResult(
            allowed=True,
        )

    async def can_execute(
        self,
        *,
        user_id: int,
        chat_id: int,
        permission: str,
    ) -> PermissionResult:
        if user_id <= 0:
            return PermissionResult(
                allowed=False,
                reason="invalid_user",
            )

        if not permission.strip():
            return PermissionResult(
                allowed=False,
                reason="invalid_permission",
            )

        return PermissionResult(
            allowed=True,
        )

    @staticmethod
    def require(
        result: PermissionResult,
    ) -> None:
        if not result.allowed:
            raise PermissionError(
                result.reason or "Permission denied."
            )