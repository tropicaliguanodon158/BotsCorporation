
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
    Глобальный middleware пользователя.

    На каждом update:

        1. гарантирует наличие пользователя;
        2. гарантирует наличие чата;
        3. обновляет профиль;
        4. для обычных сообщений фиксирует активность;
        5. выдаёт экономическую награду.

    Команды не считаются обычными сообщениями.
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
        session: AsyncSession | None = data.get("session")

        if session is None:
            raise RuntimeError(
                "UserMiddleware requires DatabaseMiddleware."
            )

        telegram_user = self._get_telegram_user(event)

        if telegram_user is None:
            return await handler(event, data)

        user_repository = UserRepository(session)

        # ====================================================================
        # USER
        # ====================================================================

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
        # CHAT
        # ====================================================================

        if isinstance(event, Message):
            chat = event.chat

            settings_repository = SettingsRepository(session)

            db_chat = await settings_repository.get_or_create_chat(
                chat_id=chat.id,
                title=chat.title,
                username=chat.username,
                chat_type=chat.type,
            )

            data["chat"] = db_chat

        # ====================================================================
        # COMMANDS
        # ====================================================================

        if isinstance(event, Message) and self._is_command(event):
            return await handler(event, data)

        # ====================================================================
        # MESSAGE ACTIVITY
        # ====================================================================

        if isinstance(event, Message):
            chat_id = event.chat.id

            message_type = self._get_message_type(event)

            tasks_repository = TasksRepository(session)

            events_service = EventsService(
                user_repository=user_repository,
                tasks_repository=tasks_repository,
            )

            await events_service.on_message(
                user_id=telegram_user.id,
                message_type=message_type,
                activity_date=datetime.now().date(),
                xp=0,
            )

            # ================================================================
            # REWARD
            # ================================================================

            rewards_service = RewardsService(
                economy_repository=EconomyRepository(session),
                settings_repository=SettingsRepository(session),
                user_repository=user_repository,
            )

            await rewards_service.message_reward(
                user_id=telegram_user.id,
                chat_id=chat_id,
                message_type=message_type,
            )

            updated_user = await user_repository.get_by_id(
                telegram_user.id,
            )

            if updated_user is not None:
                data["user"] = updated_user

        return await handler(event, data)

    # ========================================================================
    # TELEGRAM USER
    # ========================================================================

    @staticmethod
    def _get_telegram_user(
        event: TelegramObject,
    ) -> TelegramUser | None:
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
    # COMMAND CHECK
    # ========================================================================

    @staticmethod
    def _is_command(
        message: Message,
    ) -> bool:
        if not message.text:
            return False

        text = message.text.strip()

        if not text.startswith("/"):
            return False

        first_word = text.split(maxsplit=1)[0]

        return first_word.startswith("/")

    # ========================================================================
    # MESSAGE TYPE
    # ========================================================================

    @staticmethod
    def _get_message_type(
        message: Message,
    ) -> str:
        if message.photo:
            return "photo"

        if message.video:
            return "video"

        if message.text:
            return "text"

        return "other"
