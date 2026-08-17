from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


class Wallet(Base):
    """
    Кошелёк пользователя.

    Один пользователь = один кошелёк.
    """

    __tablename__ = "wallets"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
    )

    # ------------------------------------------------------------------
    # Balances
    # ------------------------------------------------------------------

    balance: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    gems: Mapped[int] = mapped_column(
        BigInteger,
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


class Transaction(Base):
    """
    Финансовая операция.

    Каждое изменение баланса должно оставлять запись здесь.

    Это позволяет:
        - видеть историю операций;
        - расследовать спорные списания;
        - делать статистику;
        - откатывать операции;
        - отслеживать действия администрации.
    """

    __tablename__ = "transactions"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Transaction
    # ------------------------------------------------------------------

    amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )

    balance_before: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )

    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Optional references
    # ------------------------------------------------------------------

    related_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )

    reference_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )