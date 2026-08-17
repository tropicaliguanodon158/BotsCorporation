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
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


# ============================================================================
# PASSIVE INCOME TYPES
# ============================================================================


class PassiveIncomeType(Base):
    """
    Тип пассивного дохода.

    Примеры:

        deposit
        mining
        investment
        event

    Все параметры можно будет менять через Founder Panel.
    """

    __tablename__ = "passive_income_types"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # ------------------------------------------------------------------
    # Basic information
    # ------------------------------------------------------------------

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

    income_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Income
    # ------------------------------------------------------------------

    # Процент доходности за один интервал.

    rate_percent: Mapped[Decimal] = mapped_column(
        Numeric(12, 6),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Через сколько секунд начисляется очередная прибыль.

    interval_seconds: Mapped[int] = mapped_column(
        Integer,
        default=3600,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Limits
    # ------------------------------------------------------------------

    min_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    max_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Activity requirement
    # ------------------------------------------------------------------

    # Сколько сообщений необходимо написать за период,
    # чтобы получать пассивный доход.

    required_messages: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Период проверки активности в днях.

    activity_period_days: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # Если False — отсутствие активности блокирует начисление.

    activity_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Duration
    # ------------------------------------------------------------------

    # 0 = бессрочно.

    duration_seconds: Mapped[int] = mapped_column(
        BigInteger,
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
# USER PASSIVE INCOME
# ============================================================================


class UserPassiveIncome(Base):
    """
    Активированный пользователем пассивный доход.

    Здесь хранится конкретный депозит/майнинг пользователя.
    """

    __tablename__ = "user_passive_income"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # ------------------------------------------------------------------
    # Owner
    # ------------------------------------------------------------------

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    passive_income_type_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "passive_income_types.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Principal
    # ------------------------------------------------------------------

    # Первоначально вложенная сумма.

    principal: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )

    # Текущий капитал.

    current_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )

    # Всего заработано за время существования.

    total_earned: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Timing
    # ------------------------------------------------------------------

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_payout_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    next_payout_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Activity
    # ------------------------------------------------------------------

    # Последний день, в котором пользователь выполнил
    # требование активности.

    activity_valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    metadata_json: Mapped[str | None] = mapped_column(
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


# ============================================================================
# PASSIVE INCOME PAYOUTS
# ============================================================================


class PassiveIncomePayout(Base):
    """
    История начислений пассивного дохода.

    Каждое начисление фиксируется отдельно.
    """

    __tablename__ = "passive_income_payouts"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    passive_income_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "user_passive_income.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Сколько начислено.

    amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )

    # Сумма капитала до начисления.

    amount_before: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )

    # Сумма капитала после начисления.

    amount_after: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )

    # Процент, использованный при расчёте.

    rate_percent: Mapped[Decimal] = mapped_column(
        Numeric(12, 6),
        nullable=False,
    )

    # Выплата была произведена или начисление только рассчитано.

    status: Mapped[str] = mapped_column(
        String(30),
        default="completed",
        nullable=False,
        index=True,
    )

    # Дополнительная информация.

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