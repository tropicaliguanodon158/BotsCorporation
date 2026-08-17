from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from aiogram.types import User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.economy import EconomyRepository
from app.database.repositories.settings import SettingsRepository
from app.database.repositories.tasks import TasksRepository
from app.database.repositories.users import UserRepository
from app.services.events import EventsService
from app.services.rewards import RewardsService


class UserMiddleware(BaseMiddleware):
    """
    Middleware автоматической регистрации пользователей.

    Дополнительно для обычных сообщений:

        - фиксирует активность;
        - обновляет счётчики сообщений;
        - выдаёт награду;
        - выдаёт XP.

    Все операции выполняются в рамках той же транзакции,
    которую создаёт DatabaseMiddleware.

    Никаких сообщений пользователю middleware не отправляет.
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
        session: AsyncSession | None = data.get(
            "session",
        )

        if session is None:
            raise RuntimeError(
                "UserMiddleware требует "
                "DatabaseMiddleware перед ним."
            )

        telegram_user = self._get_telegram_user(
            event,
        )

        if telegram_user is None:
            return await handler(
                event,
                data,
            )

        user_repository = UserRepository(
            session,
        )

        user, created = await user_repository.get_or_create(
            user_id=telegram_user.id,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            username=telegram_user.username,
        )

        if not created:
            user = await user_repository.update_profile(
                user_id=telegram_user.id,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                username=telegram_user.username,
            )

            if user is None:
                raise RuntimeError(
                    "User disappeared while updating profile."
                )

            if not user.is_active:
                await user_repository.set_active(
                    user_id=telegram_user.id,
                    is_active=True,
                )

                user = await user_repository.get_by_id(
                    telegram_user.id,
                )

                if user is None:
                    raise RuntimeError(
                        "User disappeared after activation."
                    )

        data["user"] = user

        # ====================================================================
        # MESSAGE ACTIVITY + REWARD
        # ====================================================================

        if isinstance(event, Message):
            chat_id = event.chat.id

            message_type = self._get_message_type(
                event,
            )

            tasks_repository = TasksRepository(
                session,
            )

            events_service = EventsService(
                user_repository=user_repository,
                tasks_repository=tasks_repository,
            )

            await events_service.on_message(
                user_id=telegram_user.id,
                message_type=message_type,
                activity_date=datetime.now().date(),
            )

            rewards_service = RewardsService(
                economy_repository=EconomyRepository(
                    session,
                ),
                settings_repository=SettingsRepository(
                    session,
                ),
                user_repository=user_repository,
            )

            await rewards_service.message_reward(
                user_id=telegram_user.id,
                chat_id=chat_id,
                message_type=message_type,
            )

            data["user"] = await user_repository.get_by_id(
                telegram_user.id,
            )

        return await handler(
            event,
            data,
        )

    # ========================================================================
    # TELEGRAM USER
    # ========================================================================

    @staticmethod
    def _get_telegram_user(
        event: TelegramObject,
    ) -> TelegramUser | None:
        """
        Извлекает Telegram User из события.
        """

        telegram_user = getattr(
            event,
            "from_user",
            None,
        )

        if isinstance(
            telegram_user,
            TelegramUser,
        ):
            return telegram_user

        return None

    # ========================================================================
    # MESSAGE TYPE
    # ========================================================================

    @staticmethod
    def _get_message_type(
        message: Message,
    ) -> str:
        """
        Определяет тип сообщения для экономики и активности.
        """

        if message.photo:
            return "photo"

        if message.video:
            return "video"

        if message.text:
            return "text"

        return "other"