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
# ITEMS
# ============================================================================


class Item(Base):
    """
    Предмет, существующий в игровой системе.

    Предметы создаются и настраиваются через Founder Panel.
    """

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Item type
    # ------------------------------------------------------------------

    item_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Примеры:
    #
    # cosmetic
    # weapon
    # armor
    # accessory
    # consumable
    # boost
    # quest
    # special

    # ------------------------------------------------------------------
    # Rarity
    # ------------------------------------------------------------------

    rarity: Mapped[str] = mapped_column(
        String(50),
        default="common",
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Price
    # ------------------------------------------------------------------

    price: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Consumable / effect
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

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    is_tradeable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_sellable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

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
# INVENTORY
# ============================================================================


class InventoryItem(Base):
    """
    Предмет, принадлежащий пользователю.

    Один пользователь может иметь несколько одинаковых предметов.
    """

    __tablename__ = "inventory_items"

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

    item_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # Уникальный экземпляр предмета.
    #
    # Например, для косметического предмета можно будет
    # сохранить индивидуальное имя или дополнительные данные.

    custom_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    custom_data: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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
            "item_id",
            name="uq_inventory_user_item",
        ),
    )


# ============================================================================
# EQUIPMENT
# ============================================================================


class Equipment(Base):
    """
    Экипированные предметы пользователя.

    Один слот может содержать только один предмет.
    """

    __tablename__ = "equipment"

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

    item_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    slot: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    equipped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "slot",
            name="uq_equipment_user_slot",
        ),
    )