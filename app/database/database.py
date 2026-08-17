from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import settings
from app.database.models import Base


# ============================================================================
# ENGINE
# ============================================================================

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
)


# ============================================================================
# SESSION
# ============================================================================

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================


async def init_database() -> None:
    """
    Инициализирует базу данных.

    Перед вызовом этой функции все модели должны быть
    импортированы через app.database.models.

    Благодаря этому Base.metadata содержит все таблицы проекта.
    """

    # Важно:
    # импортируем models до create_all.
    #
    # Сам факт импорта:
    #
    #     from app.database.models import Base
    #
    # приводит к регистрации всех моделей,
    # потому что models/__init__.py импортирует их все.

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )


# ============================================================================
# DATABASE SHUTDOWN
# ============================================================================


async def close_database() -> None:
    """
    Корректно закрывает соединения с базой данных.
    """

    await engine.dispose()


# ============================================================================
# SESSION HELPER
# ============================================================================


def get_session() -> AsyncSession:
    """
    Возвращает новую AsyncSession.

    Используется сервисами и репозиториями.

    Пример:

        session = get_session()

        try:
            ...
        finally:
            await session.close()
    """

    return AsyncSessionLocal()