from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


# ============================================================================
# INTERACTION TYPES
# ============================================================================


class InteractionType(Base):
    """
    Тип взаимодействия между пользователями.

    Примеры:

        kiss
        hug
        slap
        punch
        kick
        tease
        gift

    Типы создаются и редактируются через Founder Panel.
    """

    __tablename__ = "interaction_types"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # ------------------------------------------------------------------
    # Command
    # ------------------------------------------------------------------

    command: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    # Например:
    #
    # kiss
    # hug
    # slap

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Cost
    # ------------------------------------------------------------------

    cost: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    currency_type: Mapped[str] = mapped_column(
        String(30),
        default="currency",
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Cooldown
    # ------------------------------------------------------------------

    cooldown_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Target requirements
    # ------------------------------------------------------------------

    requires_target: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    allow_self_target: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Result text
    # ------------------------------------------------------------------

    # Поддерживаем шаблоны:

    # {actor}
    # {target}
    # {amount}

    success_text: Mapped[str] = mapped_column(
        Text,
        default="{actor} взаимодействует с {target}.",
        nullable=False,
    )

    # Текст при неудаче, если действие использует вероятность.

    failure_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Random mechanics
    # ------------------------------------------------------------------

    has_random_result: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    success_chance: Mapped[Decimal] = mapped_column(
        Numeric(8, 4),
        default=Decimal("100.0000"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Effects
    # ------------------------------------------------------------------

    effect_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    effect_value: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    effect_duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Например:

    # luck
    # xp
    # damage
    # heal
    # none

    # ------------------------------------------------------------------
    # Restrictions
    # ------------------------------------------------------------------

    minimum_level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    minimum_character_rank: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

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
# USER INTERACTION COOLDOWNS
# ============================================================================


class UserInteractionCooldown(Base):
    """
    Кулдаун конкретного взаимодействия пользователя.

    Храним отдельно, чтобы каждый тип взаимодействия
    имел собственный кулдаун.
    """

    __tablename__ = "user_interaction_cooldowns"

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

    interaction_type_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "interaction_types.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
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
            "interaction_type_id",
            name="uq_user_interaction_cooldown",
        ),
    )


# ============================================================================
# INTERACTION LOG
# ============================================================================


class InteractionLog(Base):
    """
    История взаимодействий между пользователями.

    Нужна для:
        - статистики;
        - достижений;
        - аудита;
        - истории действий;
        - аналитики экономики.
    """

    __tablename__ = "interaction_logs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    interaction_type_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "interaction_types.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Participants
    # ------------------------------------------------------------------

    actor_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    target_id: Mapped[int | None] = mapped_column(
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

    # ------------------------------------------------------------------
    # Financial information
    # ------------------------------------------------------------------

    cost: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    currency_type: Mapped[str] = mapped_column(
        String(30),
        default="currency",
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------

    result: Mapped[str] = mapped_column(
        String(30),
        default="success",
        nullable=False,
    )

    # success
    # failure
    # cancelled

    effect_value: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    result_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

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