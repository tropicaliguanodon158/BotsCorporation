"""
Repository for moderation system.

Отвечает за работу с:

    ModerationAction
        История действий модерации.

    UserWarning
        Активные предупреждения пользователей.

    ModerationFilter
        Автоматические фильтры чатов.

Repository не содержит Telegram API-логику.

Он не должен:
    - банить пользователя через Telegram;
    - выдавать mute;
    - удалять сообщения;
    - проверять права Telegram;
    - отправлять сообщения.

Это будет делать services/moderation.py
и соответствующие handlers.

ВАЖНО:
Repository не вызывает commit().

commit / rollback находятся выше по уровню приложения.
"""

import json
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.moderation import (
    ModerationAction,
    ModerationFilter,
    UserWarning,
)


class ModerationRepository:
    """
    Репозиторий системы модерации.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ========================================================================
    # MODERATION ACTIONS
    # ========================================================================

    async def create_action(
        self,
        *,
        moderator_id: int | None,
        target_user_id: int,
        chat_id: int,
        action_type: str,
        reason: str | None = None,
        duration_seconds: int | None = None,
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ModerationAction:
        """
        Создать запись о действии модерации.

        Примеры action_type:

            warn
            mute
            unmute
            kick
            ban
            unban
            delete_message
            restrict
            unrestrict
        """

        if duration_seconds is not None and duration_seconds < 0:
            raise ValueError(
                "duration_seconds cannot be negative."
            )

        metadata_json: str | None = None

        if metadata is not None:
            metadata_json = json.dumps(
                metadata,
                ensure_ascii=False,
                default=str,
            )

        action = ModerationAction(
            moderator_id=moderator_id,
            target_user_id=target_user_id,
            chat_id=chat_id,
            action_type=action_type,
            reason=reason,
            duration_seconds=duration_seconds,
            expires_at=expires_at,
            metadata_json=metadata_json,
        )

        self.session.add(action)

        await self.session.flush()

        return action

    async def get_action(
        self,
        action_id: int,
    ) -> ModerationAction | None:
        """
        Получить конкретное действие модерации.
        """

        result = await self.session.execute(
            select(ModerationAction).where(
                ModerationAction.id == action_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_user_actions(
        self,
        *,
        target_user_id: int,
        chat_id: int | None = None,
        action_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[ModerationAction]:
        """
        Получить историю модерации пользователя.

        Можно дополнительно ограничить:
            - чатом;
            - типом действия.
        """

        limit = max(1, min(limit, 1000))
        offset = max(0, offset)

        query = select(ModerationAction).where(
            ModerationAction.target_user_id == target_user_id,
        )

        if chat_id is not None:
            query = query.where(
                ModerationAction.chat_id == chat_id,
            )

        if action_type is not None:
            query = query.where(
                ModerationAction.action_type == action_type,
            )

        query = (
            query
            .order_by(
                ModerationAction.created_at.desc(),
                ModerationAction.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    async def get_chat_actions(
        self,
        *,
        chat_id: int,
        action_type: str | None = None,
        moderator_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ModerationAction]:
        """
        Получить историю модерации конкретного чата.
        """

        limit = max(1, min(limit, 1000))
        offset = max(0, offset)

        query = select(ModerationAction).where(
            ModerationAction.chat_id == chat_id,
        )

        if action_type is not None:
            query = query.where(
                ModerationAction.action_type == action_type,
            )

        if moderator_id is not None:
            query = query.where(
                ModerationAction.moderator_id == moderator_id,
            )

        query = (
            query
            .order_by(
                ModerationAction.created_at.desc(),
                ModerationAction.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    async def get_expired_actions(
        self,
        *,
        now: datetime,
        limit: int = 100,
    ) -> Sequence[ModerationAction]:
        """
        Получить временные действия, срок которых истёк.

        В дальнейшем scheduler сможет использовать это
        для автоматического снятия ограничений.
        """

        limit = max(1, min(limit, 1000))

        result = await self.session.execute(
            select(ModerationAction)
            .where(
                ModerationAction.expires_at.is_not(None),
                ModerationAction.expires_at <= now,
            )
            .order_by(
                ModerationAction.expires_at.asc(),
            )
            .limit(limit)
        )

        return result.scalars().all()

    # ========================================================================
    # WARNINGS
    # ========================================================================

    async def create_warning(
        self,
        *,
        user_id: int,
        chat_id: int,
        moderator_id: int | None,
        reason: str | None = None,
        expires_at: datetime | None = None,
    ) -> UserWarning:
        """
        Создать активное предупреждение.
        """

        warning = UserWarning(
            user_id=user_id,
            chat_id=chat_id,
            moderator_id=moderator_id,
            reason=reason,
            expires_at=expires_at,
            is_active=True,
        )

        self.session.add(warning)

        await self.session.flush()

        return warning

    async def get_warning(
        self,
        warning_id: int,
    ) -> UserWarning | None:
        """
        Получить предупреждение по ID.
        """

        result = await self.session.execute(
            select(UserWarning).where(
                UserWarning.id == warning_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_active_warnings(
        self,
        *,
        user_id: int,
        chat_id: int,
        now: datetime | None = None,
    ) -> Sequence[UserWarning]:
        """
        Получить активные предупреждения пользователя.

        Если передан now, просроченные предупреждения
        не считаются активными.
        """

        query = select(UserWarning).where(
            UserWarning.user_id == user_id,
            UserWarning.chat_id == chat_id,
            UserWarning.is_active.is_(True),
        )

        if now is not None:
            query = query.where(
                (
                    UserWarning.expires_at.is_(None)
                )
                |
                (
                    UserWarning.expires_at > now
                )
            )

        query = query.order_by(
            UserWarning.created_at.asc(),
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    async def count_active_warnings(
        self,
        *,
        user_id: int,
        chat_id: int,
        now: datetime | None = None,
    ) -> int:
        """
        Получить количество активных предупреждений.

        Сделано через получение записей, чтобы не привязывать
        repository к конкретному SQL dialect.
        """

        warnings = await self.get_active_warnings(
            user_id=user_id,
            chat_id=chat_id,
            now=now,
        )

        return len(warnings)

    async def deactivate_warning(
        self,
        warning_id: int,
    ) -> bool:
        """
        Сделать предупреждение неактивным.
        """

        warning = await self.get_warning(
            warning_id,
        )

        if warning is None:
            return False

        if not warning.is_active:
            return True

        warning.is_active = False

        await self.session.flush()

        return True

    async def deactivate_user_warnings(
        self,
        *,
        user_id: int,
        chat_id: int,
    ) -> int:
        """
        Снять все активные предупреждения пользователя
        в конкретном чате.

        Возвращает количество изменённых предупреждений.
        """

        warnings = await self.get_active_warnings(
            user_id=user_id,
            chat_id=chat_id,
        )

        count = 0

        for warning in warnings:
            warning.is_active = False
            count += 1

        await self.session.flush()

        return count

    async def deactivate_expired_warnings(
        self,
        *,
        now: datetime,
        limit: int = 500,
    ) -> int:
        """
        Деактивировать истёкшие предупреждения.

        Будет использоваться фоновой задачей.
        """

        limit = max(1, min(limit, 1000))

        result = await self.session.execute(
            select(UserWarning)
            .where(
                UserWarning.is_active.is_(True),
                UserWarning.expires_at.is_not(None),
                UserWarning.expires_at <= now,
            )
            .order_by(
                UserWarning.expires_at.asc(),
            )
            .limit(limit)
        )

        warnings = result.scalars().all()

        count = 0

        for warning in warnings:
            warning.is_active = False
            count += 1

        await self.session.flush()

        return count

    # ========================================================================
    # MODERATION FILTERS
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
        is_active: bool = True,
    ) -> ModerationFilter:
        """
        Создать автоматический фильтр.
        """

        pattern = pattern.strip()

        if not pattern:
            raise ValueError(
                "Filter pattern cannot be empty."
            )

        allowed_match_types = {
            "exact",
            "contains",
            "starts_with",
            "ends_with",
            "regex",
        }

        if match_type not in allowed_match_types:
            raise ValueError(
                f"Unsupported match_type: {match_type}"
            )

        allowed_actions = {
            "delete",
            "warn",
            "mute",
            "ban",
        }

        if action_type not in allowed_actions:
            raise ValueError(
                f"Unsupported action_type: {action_type}"
            )

        if duration_seconds is not None and duration_seconds < 0:
            raise ValueError(
                "duration_seconds cannot be negative."
            )

        moderation_filter = ModerationFilter(
            chat_id=chat_id,
            pattern=pattern,
            match_type=match_type,
            action_type=action_type,
            duration_seconds=duration_seconds,
            reason=reason,
            is_active=is_active,
        )

        self.session.add(moderation_filter)

        await self.session.flush()

        return moderation_filter

    async def get_filter(
        self,
        filter_id: int,
    ) -> ModerationFilter | None:
        """
        Получить фильтр по ID.
        """

        result = await self.session.execute(
            select(ModerationFilter).where(
                ModerationFilter.id == filter_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_active_filters(
        self,
        *,
        chat_id: int,
    ) -> Sequence[ModerationFilter]:
        """
        Получить активные фильтры чата.
        """

        result = await self.session.execute(
            select(ModerationFilter)
            .where(
                ModerationFilter.chat_id == chat_id,
                ModerationFilter.is_active.is_(True),
            )
            .order_by(
                ModerationFilter.id.asc(),
            )
        )

        return result.scalars().all()

    async def get_chat_filters(
        self,
        *,
        chat_id: int,
        include_inactive: bool = False,
        limit: int = 500,
        offset: int = 0,
    ) -> Sequence[ModerationFilter]:
        """
        Получить фильтры чата.

        Founder Panel сможет использовать
        include_inactive=True для управления всеми фильтрами.
        """

        limit = max(1, min(limit, 1000))
        offset = max(0, offset)

        query = select(ModerationFilter).where(
            ModerationFilter.chat_id == chat_id,
        )

        if not include_inactive:
            query = query.where(
                ModerationFilter.is_active.is_(True),
            )

        query = (
            query
            .order_by(
                ModerationFilter.id.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    async def update_filter(
        self,
        filter_id: int,
        **values: object,
    ) -> ModerationFilter | None:
        """
        Изменить настройки фильтра.

        Предназначено в первую очередь для Founder Panel.
        """

        allowed_fields = {
            "pattern",
            "match_type",
            "action_type",
            "duration_seconds",
            "reason",
            "is_active",
        }

        invalid_fields = set(values) - allowed_fields

        if invalid_fields:
            raise ValueError(
                "Unsupported filter fields: "
                + ", ".join(sorted(invalid_fields))
            )

        moderation_filter = await self.get_filter(
            filter_id,
        )

        if moderation_filter is None:
            return None

        if "pattern" in values:
            pattern = str(values["pattern"]).strip()

            if not pattern:
                raise ValueError(
                    "Filter pattern cannot be empty."
                )

            values["pattern"] = pattern

        if "match_type" in values:
            match_type = str(values["match_type"])

            allowed_match_types = {
                "exact",
                "contains",
                "starts_with",
                "ends_with",
                "regex",
            }

            if match_type not in allowed_match_types:
                raise ValueError(
                    f"Unsupported match_type: {match_type}"
                )

        if "action_type" in values:
            action_type = str(values["action_type"])

            allowed_actions = {
                "delete",
                "warn",
                "mute",
                "ban",
            }

            if action_type not in allowed_actions:
                raise ValueError(
                    f"Unsupported action_type: {action_type}"
                )

        if "duration_seconds" in values:
            duration = values["duration_seconds"]

            if duration is not None and int(duration) < 0:
                raise ValueError(
                    "duration_seconds cannot be negative."
                )

        for field, value in values.items():
            setattr(
                moderation_filter,
                field,
                value,
            )

        await self.session.flush()

        return moderation_filter

    async def deactivate_filter(
        self,
        filter_id: int,
    ) -> bool:
        """
        Выключить фильтр.
        """

        moderation_filter = await self.get_filter(
            filter_id,
        )

        if moderation_filter is None:
            return False

        moderation_filter.is_active = False

        await self.session.flush()

        return True

    async def activate_filter(
        self,
        filter_id: int,
    ) -> bool:
        """
        Включить фильтр.
        """

        moderation_filter = await self.get_filter(
            filter_id,
        )

        if moderation_filter is None:
            return False

        moderation_filter.is_active = True

        await self.session.flush()

        return True

    async def delete_filter(
        self,
        filter_id: int,
    ) -> bool:
        """
        Физически удалить фильтр.

        Для обычной работы предпочтительнее deactivate_filter().
        Полное удаление пригодится Founder Panel.
        """

        moderation_filter = await self.get_filter(
            filter_id,
        )

        if moderation_filter is None:
            return False

        await self.session.delete(
            moderation_filter,
        )

        await self.session.flush()

        return True