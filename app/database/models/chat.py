from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


# ============================================================================
# CHAT
# ============================================================================


class Chat(Base):
    """
    Telegram-чат, в котором работает бот.

    Все настройки конкретного чата хранятся здесь или
    в связанных конфигурационных сущностях.
    """

    __tablename__ = "chats"

    # ------------------------------------------------------------------
    # Telegram
    # ------------------------------------------------------------------

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    chat_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="group",
    )

    # group
    # supergroup
    # channel

    # ------------------------------------------------------------------
    # Bot status
    # ------------------------------------------------------------------

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    is_initialized: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Economy
    # ------------------------------------------------------------------

    economy_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    currency_name: Mapped[str] = mapped_column(
        String(50),
        default="монет",
        nullable=False,
    )

    currency_symbol: Mapped[str] = mapped_column(
        String(10),
        default="🪙",
        nullable=False,
    )

    # Награда за обычное текстовое сообщение.

    message_reward: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("1.00"),
        nullable=False,
    )

    # Награда за фотографию.

    photo_reward: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("3.00"),
        nullable=False,
    )

    # Награда за видео.

    video_reward: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("5.00"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Anti-abuse
    # ------------------------------------------------------------------

    # Минимальный интервал между сообщениями,
    # за которые выдаётся экономическая награда.

    economy_message_cooldown_seconds: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Moderation
    # ------------------------------------------------------------------

    moderation_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    automod_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    antiflood_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Games
    # ------------------------------------------------------------------

    games_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    interactions_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Character system
    # ------------------------------------------------------------------

    characters_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    abilities_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Passive income
    # ------------------------------------------------------------------

    passive_income_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Experience / levels
    # ------------------------------------------------------------------

    leveling_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Welcome / notifications
    # ------------------------------------------------------------------

    welcome_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    welcome_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    logging_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    log_chat_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    timezone: Mapped[str] = mapped_column(
        String(100),
        default="Europe/Warsaw",
        nullable=False,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        default="ru",
        nullable=False,
    )

    # Произвольные настройки.

    settings_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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

    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )