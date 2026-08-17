from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


# ============================================================================
# MODERATION ACTIONS
# ============================================================================


class ModerationAction(Base):
    """
    История действий модерации.

    Каждое предупреждение, мут, кик, бан и т.д.
    записывается отдельной записью.
    """

    __tablename__ = "moderation_actions"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # ------------------------------------------------------------------
    # Participants
    # ------------------------------------------------------------------

    moderator_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    target_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Action
    # ------------------------------------------------------------------

    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Примеры:
    #
    # warn
    # mute
    # unmute
    # kick
    # ban
    # unban
    # delete_message
    # restrict
    # unrestrict

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Duration
    # ------------------------------------------------------------------

    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Extra information
    # ------------------------------------------------------------------

    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )


# ============================================================================
# USER WARNINGS
# ============================================================================


class UserWarning(Base):
    """
    Активное предупреждение пользователя.

    История всех предупреждений дополнительно хранится
    в ModerationAction.
    """

    __tablename__ = "user_warnings"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    moderator_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Если предупреждение временное.

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


# ============================================================================
# MODERATION FILTERS
# ============================================================================


class ModerationFilter(Base):
    """
    Автоматический фильтр модерации.

    Позволяет создавать фильтры без изменения кода.

    Например:

        слово -> удалить сообщение
        слово -> warning
        слово -> mute
    """

    __tablename__ = "moderation_filters"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    # Что ищем.

    pattern: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Тип совпадения:
    #
    # exact
    # contains
    # starts_with
    # ends_with
    # regex

    match_type: Mapped[str] = mapped_column(
        String(50),
        default="contains",
        nullable=False,
    )

    # Что делать при срабатывании.

    action_type: Mapped[str] = mapped_column(
        String(50),
        default="delete",
        nullable=False,
    )

    # Возможные действия:
    #
    # delete
    # warn
    # mute
    # ban

    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

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