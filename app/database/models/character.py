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
# RACES
# ============================================================================


class Race(Base):
    """
    Игровая раса персонажа.

    Расу можно создавать и редактировать через Founder Panel.
    """

    __tablename__ = "races"

    # SQLite autoincrement корректно работает с INTEGER PRIMARY KEY.
    id: Mapped[int] = mapped_column(
        Integer,
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

    # Базовые характеристики расы.

    base_hp: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
    )

    base_strength: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    base_defense: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    base_luck: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    base_speed: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    base_intelligence: Mapped[int] = mapped_column(
        Integer,
        default=10,
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
# CHARACTER RANKS
# ============================================================================


class CharacterRank(Base):
    """
    Ранг игрового персонажа.

    Ранг влияет на характеристики и открывает игровые возможности.
    """

    __tablename__ = "character_ranks"

    # SQLite autoincrement корректно работает с INTEGER PRIMARY KEY.
    id: Mapped[int] = mapped_column(
        Integer,
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

    # Порядковый номер ранга.
    # Например:
    # 1 = Новобранец
    # 2 = Искатель
    # 3 = Воин
    # ...

    level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    # Требования для получения ранга.

    required_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    required_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    required_reputation: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Бонусы ранга.

    hp_bonus: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    strength_bonus: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    defense_bonus: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    luck_bonus: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    speed_bonus: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    intelligence_bonus: Mapped[int] = mapped_column(
        Integer,
        default=0,
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
# ABILITIES
# ============================================================================


class Ability(Base):
    """
    Игровая способность.

    Способности хранятся как данные и могут создаваться
    через Founder Panel.
    """

    __tablename__ = "abilities"

    # SQLite autoincrement корректно работает с INTEGER PRIMARY KEY.
    id: Mapped[int] = mapped_column(
        Integer,
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

    # Тип эффекта.

    ability_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Сила эффекта.
    #
    # Конкретная интерпретация зависит от ability_type.
    #
    # Например:
    # 15 = +15%
    # 5  = +5 к характеристике

    effect_value: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Продолжительность эффекта в секундах.
    # 0 = постоянный эффект.

    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Cooldown в секундах.

    cooldown_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
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
# CHARACTERS
# ============================================================================


class Character(Base):
    """
    Игровой персонаж пользователя.
    """

    __tablename__ = "characters"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )

    # ------------------------------------------------------------------
    # Character information
    # ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    race_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("races.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    rank_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("character_ranks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Character level
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

    # ------------------------------------------------------------------
    # Current stats
    # ------------------------------------------------------------------

    hp: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
    )

    max_hp: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
    )

    strength: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    defense: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    luck: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    speed: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    intelligence: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Customization
    # ------------------------------------------------------------------

    title: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
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


# ============================================================================
# CHARACTER ABILITIES
# ============================================================================


class CharacterAbility(Base):
    """
    Связь персонажа со способностью.

    Позволяет одному персонажу иметь несколько способностей.
    """

    __tablename__ = "character_abilities"

    # SQLite autoincrement корректно работает с INTEGER PRIMARY KEY.
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("characters.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ability_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("abilities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Текущий cooldown способности.
    # NULL = способность доступна.

    cooldown_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Активный временный эффект.

    effect_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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