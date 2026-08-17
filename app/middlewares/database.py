from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.database import AsyncSessionLocal


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware для работы с SQLAlchemy AsyncSession.

    Для каждого Telegram update:

        1. создаётся новая AsyncSession;
        2. session передаётся в handler;
        3. handler выполняется;
        4. при успехе выполняется commit;
        5. при ошибке выполняется rollback;
        6. session закрывается.

    Репозитории и сервисы получают эту же session.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal,
    ) -> None:
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[
            [TelegramObject, dict[str, Any]],
            Awaitable[Any],
        ],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Создаёт транзакцию на время обработки одного update.
        """

        async with self.session_factory() as session:
            data["session"] = session

            try:
                result = await handler(
                    event,
                    data,
                )

                await session.commit()

                return result

            except Exception:
                await session.rollback()
                raise