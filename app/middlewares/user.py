from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types import User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.repositories.users import UserRepository


class UserMiddleware(BaseMiddleware):
    """
    Middleware автоматической регистрации Telegram-пользователей.

    Для каждого Telegram Update:

        1. Получает Telegram User.
        2. Получает/создаёт пользователя через UserRepository.
        3. Обновляет актуальные Telegram-данные.
        4. Передаёт SQLAlchemy User в handler через data["user"].

    Middleware не содержит SQL.
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

        repository = UserRepository(
            session,
        )

        user, created = await repository.get_or_create(
            user_id=telegram_user.id,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            username=telegram_user.username,
        )

        if not created:
            user = await repository.update_profile(
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
                await repository.set_active(
                    user_id=telegram_user.id,
                    is_active=True,
                )

                user = await repository.get_by_id(
                    telegram_user.id,
                )

                if user is None:
                    raise RuntimeError(
                        "User disappeared after activation."
                    )

        data["user"] = user

        return await handler(
            event,
            data,
        )

    @staticmethod
    def _get_telegram_user(
        event: TelegramObject,
    ) -> TelegramUser | None:
        """
        Извлекает Telegram User из события.

        Если конкретный update не содержит пользователя,
        middleware просто пропускает его дальше.
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