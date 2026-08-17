from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


# ============================================================================
# GAMES
# ============================================================================


class Game(Base):
    """
    Игровая сессия.

    Типы игр:

        roulette
        blackjack
        dice
        duel
        coinflip
    """

    __tablename__ = "games"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    game_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="created",
        nullable=False,
        index=True,
    )

    chat_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )

    creator_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    winner_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    pot: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    game_data: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    round_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# ============================================================================
# GAME PLAYERS
# ============================================================================


class GamePlayer(Base):
    """
    Участник игровой сессии.

    Один пользователь может находиться
    в конкретной игре только один раз.
    """

    __tablename__ = "game_players"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    game_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "games.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    bet: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    payout: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    result: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    player_data: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "user_id",
            name="uq_game_player",
        ),
    )


# ============================================================================
# GAME BETS
# ============================================================================


class GameBet(Base):
    """
    Отдельная ставка.

    Используется для финансового аудита.

    Одна и та же ставка пользователя в рамках
    конкретной игровой сессии не должна создаваться
    несколько раз.
    """

    __tablename__ = "game_bets"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    game_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "games.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )

    bet_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    selection: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    payout: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "user_id",
            name="uq_game_bet_user",
        ),
    )
