from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


class User(Base):
    """
    Пользователь Telegram.

    Здесь хранятся данные самого Telegram-пользователя.
    Данные RPG-персонажа, инвентарь и экономика будут
    вынесены в отдельные таблицы.
    """

    __tablename__ = "users"

    # ------------------------------------------------------------------
    # Telegram
    # ------------------------------------------------------------------

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    last_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Progression
    # ------------------------------------------------------------------

    level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    reputation: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Activity
    # ------------------------------------------------------------------

    message_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    daily_message_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )