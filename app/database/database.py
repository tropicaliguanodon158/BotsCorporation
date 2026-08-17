
from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import settings
from app.database.models import Base


# ============================================================================
# DATABASE URL
# ============================================================================

DATABASE_URL = settings.DATABASE_URL


# ============================================================================
# ENGINE
# ============================================================================

_engine_kwargs: dict = {
    "echo": settings.DATABASE_ECHO,
    "pool_pre_ping": True,
}


# SQLite не нуждается в большом connection pool.
#
# Для локального запуска на ноутбуке:
#     - минимальное потребление памяти;
#     - меньше открытых соединений;
#     - WAL для лучшей конкурентности чтения/записи;
#     - timeout вместо мгновенного "database is locked".
#
# Для PostgreSQL используется небольшой pool.
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(
        {
            "connect_args": {
                "check_same_thread": False,
                "timeout": 30,
            },
        }
    )

else:
    _engine_kwargs.update(
        {
            "pool_size": 5,
            "max_overflow": 2,
            "pool_timeout": 30,
            "pool_recycle": 1800,
        }
    )


engine = create_async_engine(
    DATABASE_URL,
    **_engine_kwargs,
)


# ============================================================================
# SQLITE OPTIMIZATION
# ============================================================================


if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(
        engine.sync_engine,
        "connect",
    )
    def _configure_sqlite(
        dbapi_connection,
        connection_record,
    ) -> None:
        """
        Настройки SQLite для длительной работы бота.

        WAL:
            позволяет чтениям продолжаться во время записи.

        NORMAL:
            хороший баланс между безопасностью и скоростью.

        foreign_keys:
            обязательно включаем каскадные FK.
        """

        cursor = dbapi_connection.cursor()

        cursor.execute(
            "PRAGMA journal_mode=WAL"
        )

        cursor.execute(
            "PRAGMA synchronous=NORMAL"
        )

        cursor.execute(
            "PRAGMA foreign_keys=ON"
        )

        cursor.execute(
            "PRAGMA busy_timeout=30000"
        )

        cursor.close()


# ============================================================================
# SESSION
# ============================================================================


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================


async def init_database() -> None:
    """
    Инициализирует базу данных.

    На этапе разработки create_all используется для
    создания отсутствующих таблиц.

    В production после стабилизации схемы необходимо
    перейти на Alembic migrations.
    """

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )


# ============================================================================
# DATABASE SHUTDOWN
# ============================================================================


async def close_database() -> None:
    """
    Корректно закрывает connection pool.
    """

    await engine.dispose()


# ============================================================================
# SESSION HELPER
# ============================================================================


def get_session() -> AsyncSession:
    """
    Создаёт новую AsyncSession.

    В обычных Telegram handlers рекомендуется
    использовать session, предоставленную
    DatabaseMiddleware.

    Этот helper оставлен для фоновых задач
    и отдельных сервисных операций.
    """

    return AsyncSessionLocal()


__all__ = [
    "engine",
    "AsyncSessionLocal",
    "init_database",
    "close_database",
    "get_session",
]
