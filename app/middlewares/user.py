from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User


class UserMiddleware(BaseMiddleware):
    """
    Middleware автоматической регистрации Telegram-пользователей.

    Для каждого Telegram Update:

        1. Получаем Telegram User.
        2. Проверяем его наличие в БД.
        3. Если пользователя нет — создаём.
        4. Если пользователь существует — обновляем
           актуальные Telegram-данные.
        5. Передаём объект User в handler через:
               data["user"]

    После этого любой handler может получать:

        async def handler(message, user):
            ...

    Вместе с DatabaseMiddleware:

        async def handler(message, session, user):
            ...
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
                "UserMiddleware требует DatabaseMiddleware "
                "сначала."
            )

        telegram_user = self._get_telegram_user(event)

        # Некоторые Telegram updates могут не содержать
        # пользователя.
        #
        # Например, отдельные системные события.
        #
        # В таком случае просто пропускаем UserMiddleware.

        if telegram_user is None:
            return await handler(event, data)

        user = await self._get_or_create_user(
            session=session,
            telegram_user=telegram_user,
        )

        # Передаём SQLAlchemy User в handler.

        data["user"] = user

        return await handler(event, data)

    @staticmethod
    def _get_telegram_user(
        event: TelegramObject,
    ) -> TelegramUser | None:
        """
        Пытается получить Telegram User из update.

        Aiogram передаёт разные типы событий:
            Message
            CallbackQuery
            InlineQuery
            ChatMemberUpdated
            и т.д.

        Поэтому не привязываемся к одному конкретному типу.
        """

        # Большинство событий aiogram содержит поле `from_user`.

        telegram_user = getattr(
            event,
            "from_user",
            None,
        )

        if isinstance(telegram_user, TelegramUser):
            return telegram_user

        # Некоторые события могут содержать пользователя
        # в других полях.

        return None

    @staticmethod
    async def _get_or_create_user(
        session: AsyncSession,
        telegram_user: TelegramUser,
    ) -> User:
        """
        Получает пользователя из БД либо создаёт его.
        """

        result = await session.execute(
            select(User).where(
                User.id == telegram_user.id,
            )
        )

        user = result.scalar_one_or_none()

        # --------------------------------------------------------------
        # Новый пользователь
        # --------------------------------------------------------------

        if user is None:
            user = User(
                id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                is_active=True,
                level=1,
                xp=0,
                reputation=0,
                message_count=0,
                daily_message_count=0,
            )

            session.add(user)

            # flush нужен для того, чтобы SQLAlchemy отправил INSERT
            # в текущую транзакцию.
            #
            # При этом commit здесь НЕ выполняем.
            #
            # Commit полностью контролируется DatabaseMiddleware.

            await session.flush()

            return user

        # --------------------------------------------------------------
        # Существующий пользователь
        # --------------------------------------------------------------

        changed = False

        if user.username != telegram_user.username:
            user.username = telegram_user.username
            changed = True

        if user.first_name != telegram_user.first_name:
            user.first_name = telegram_user.first_name
            changed = True

        if user.last_name != telegram_user.last_name:
            user.last_name = telegram_user.last_name
            changed = True

        # Если пользователь ранее был деактивирован,
        # но снова взаимодействует с ботом —
        # автоматически возвращаем его в активное состояние.

        if not user.is_active:
            user.is_active = True
            changed = True

        if changed:
            await session.flush()

        return user