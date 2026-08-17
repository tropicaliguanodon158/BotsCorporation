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
# CASES
# ============================================================================


class Case(Base):
    """
    Игровой кейс.

    Пример:

        🎁 Обычный кейс
        Цена: 500 монет

    Содержимое кейса определяется через CaseReward.
    """

    __tablename__ = "cases"

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
    # Price
    # ------------------------------------------------------------------

    price: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Валюта, которой оплачивается кейс.
    #
    # currency
    # gems

    currency_type: Mapped[str] = mapped_column(
        String(30),
        default="currency",
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

    # Можно ли покупать кейс напрямую.
    #
    # False удобно для:
    # - ивентов;
    # - админских наград;
    # - специальных кейсов.

    is_purchasable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    image_file_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    custom_data: Mapped[str | None] = mapped_column(
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


# ============================================================================
# CASE REWARDS
# ============================================================================


class CaseReward(Base):
    """
    Возможная награда из кейса.

    Вероятности всех активных наград одного кейса должны
    корректно формировать таблицу вероятностей.

    Пример:

        Обычная награда      70%
        Редкая награда       20%
        Эпическая награда     9%
        Легендарная           1%
    """

    __tablename__ = "case_rewards"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    case_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Reward type
    # ------------------------------------------------------------------

    reward_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Возможные типы:
    #
    # item
    # currency
    # gems
    # xp
    # ability
    #
    # В дальнейшем можно добавить другие типы.

    # ------------------------------------------------------------------
    # Reward reference
    # ------------------------------------------------------------------

    item_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    ability_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("abilities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Amount
    # ------------------------------------------------------------------

    min_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("1.00"),
        nullable=False,
    )

    max_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("1.00"),
        nullable=False,
    )

    # Для XP / gems / currency значение может быть:
    #
    # min_amount = 100
    # max_amount = 500
    #
    # Для предмета:
    #
    # min_amount = 1
    # max_amount = 1

    # ------------------------------------------------------------------
    # Probability
    # ------------------------------------------------------------------

    probability: Mapped[Decimal] = mapped_column(
        Numeric(12, 8),
        nullable=False,
    )

    # Примеры:
    #
    # 70.00000000
    # 20.00000000
    #  9.00000000
    #  1.00000000

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    display_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    rarity: Mapped[str] = mapped_column(
        String(50),
        default="common",
        nullable=False,
        index=True,
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
# CASE OPENINGS
# ============================================================================


class CaseOpening(Base):
    """
    История открытия кейсов.

    Нужна для:
        - статистики;
        - аудита;
        - истории игрока;
        - защиты от спорных ситуаций;
        - анализа экономики.
    """

    __tablename__ = "case_openings"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    case_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Какая награда выпала.

    reward_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("case_rewards.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    reward_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    reward_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    item_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("items.id", ondelete="SET NULL"),
        nullable=True,
    )

    # За сколько был открыт кейс.

    price_paid: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    currency_type: Mapped[str] = mapped_column(
        String(30),
        default="currency",
        nullable=False,
    )

    # Сохраняем дополнительную информацию о результате.

    result_data: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )