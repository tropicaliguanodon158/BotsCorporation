from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


# ============================================================================
# ADMIN LEVELS
# ============================================================================


class AdminLevel(Base):
    """
    Уровень административного доступа.

    Уровни полностью управляются из Founder Panel.
    """

    __tablename__ = "admin_levels"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    # Чем выше число, тем выше уровень доступа.

    level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    # Уровень нельзя купить за игровую валюту.

    is_purchasable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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


# ============================================================================
# PERMISSIONS
# ============================================================================


class Permission(Base):
    """
    Отдельное административное разрешение.

    Примеры:

        moderation.warn
        moderation.mute
        moderation.kick
        moderation.ban
        moderation.delete

        economy.give
        economy.take

        users.view
        users.edit

        settings.view
        settings.edit

        founder.panel
    """

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    key: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


# ============================================================================
# ADMIN LEVEL PERMISSIONS
# ============================================================================


class AdminLevelPermission(Base):
    """
    Связь административного уровня с permission.
    """

    __tablename__ = "admin_level_permissions"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    admin_level_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("admin_levels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    permission_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "admin_level_id",
            "permission_id",
            name="uq_admin_level_permission",
        ),
    )


# ============================================================================
# CHAT ADMIN ASSIGNMENTS
# ============================================================================


class ChatAdmin(Base):
    """
    Назначение пользователя администратором конкретного чата.

    Один пользователь может иметь разные уровни в разных чатах.
    """

    __tablename__ = "chat_admins"

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

    admin_level_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("admin_levels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    assigned_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
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

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "chat_id",
            name="uq_chat_admin_user_chat",
        ),
    )


# ============================================================================
# ADMIN ACTION LOG
# ============================================================================


class AdminActionLog(Base):
    """
    Аудит действий администрации.

    Отдельно от ModerationAction, потому что сюда попадают
    не только наказания пользователей.

    Например:

        изменение настройки;
        выдача админки;
        снятие админки;
        изменение экономики;
        создание предмета;
        изменение ранга.
    """

    __tablename__ = "admin_action_logs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    admin_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    chat_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    target_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    target_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )