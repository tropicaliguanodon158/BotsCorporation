from __future__ import annotations

from sqlalchemy import event, inspect, text

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import settings
from app.database.models import Base


DATABASE_URL = settings.DATABASE_URL


_engine_kwargs: dict = {
    "echo": settings.DATABASE_ECHO,
    "pool_pre_ping": True,
}


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


if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(
        engine.sync_engine,
        "connect",
    )
    def _configure_sqlite(
        dbapi_connection,
        connection_record,
    ) -> None:
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


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def _ensure_sqlite_schema(
    connection: AsyncConnection,
) -> None:
    """
    Небольшой встроенный schema upgrade для локальной SQLite БД.

    Используется только для безопасного перехода
    существующей development-базы на текущую схему.

    Полноценные миграции в дальнейшем лучше перевести
    на Alembic.
    """

    if not DATABASE_URL.startswith("sqlite"):
        return

    def inspect_schema(sync_connection) -> None:
        inspector = inspect(sync_connection)

        table_names = inspector.get_table_names()

        # --------------------------------------------------------------
        # Users
        # --------------------------------------------------------------

        if "users" in table_names:
            user_columns = {
                column["name"]
                for column in inspector.get_columns(
                    "users"
                )
            }

            if "last_hourly_at" not in user_columns:
                sync_connection.execute(
                    text(
                        """
                        ALTER TABLE users
                        ADD COLUMN last_hourly_at DATETIME
                        """
                    )
                )

        # --------------------------------------------------------------
        # Transactions
        # --------------------------------------------------------------

        if "transactions" not in table_names:
            return

        unique_constraints = (
            inspector.get_unique_constraints(
                "transactions"
            )
        )

        existing_names = {
            constraint.get("name")
            for constraint in unique_constraints
        }

        target_name = (
            "uq_transactions_user_reference"
        )

        if target_name in existing_names:
            return

        columns = {
            column["name"]
            for column in inspector.get_columns(
                "transactions"
            )
        }

        if {
            "user_id",
            "reference_id",
        } - columns:
            return

        sync_connection.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                uq_transactions_user_reference
                ON transactions (
                    user_id,
                    reference_id
                )
                WHERE reference_id IS NOT NULL
                """
            )
        )

    await connection.run_sync(
        inspect_schema
    )


async def init_database() -> None:
    """
    Создаёт отсутствующие таблицы и выполняет
    небольшие совместимые schema upgrades.
    """

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )

        await _ensure_sqlite_schema(
            connection
        )


async def close_database() -> None:
    """
    Корректно закрывает connection pool.
    """

    await engine.dispose()


def get_session() -> AsyncSession:
    """
    Создаёт отдельную AsyncSession.

    Для обычных handlers следует использовать
    session из DatabaseMiddleware.
    """

    return AsyncSessionLocal()


__all__ = [
    "engine",
    "AsyncSessionLocal",
    "init_database",
    "close_database",
    "get_session",
]