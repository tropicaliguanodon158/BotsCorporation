from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
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
# GAMES
# ============================================================================


class Game(Base):
    """
    Игровая сессия.

    Примеры game_type:

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

    # Возможные состояния:
    #
    # created
    # waiting
    # active
    # finished
    # cancelled

    chat_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )

    creator_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    winner_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Общая сумма ставок/банка игры.

    pot: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Произвольные данные состояния игры.

    game_data: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Уникальный идентификатор раунда,
    # который можно показывать в логах.

    round_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
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
    """

    __tablename__ = "game_players"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    game_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Ставка игрока.

    bet: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Сколько игрок получил после завершения игры.

    payout: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Результат игрока.

    result: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Возможные значения:
    #
    # winner
    # loser
    # draw
    # bust
    # cancelled

    # Индивидуальное состояние игрока.

    player_data: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


# ============================================================================
# GAME BETS
# ============================================================================


class GameBet(Base):
    """
    Отдельная ставка в игре.

    Используется для детального финансового аудита.
    """

    __tablename__ = "game_bets"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    game_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
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

    # Например:
    #
    # red
    # black
    # number
    # odd
    # even
    # blackjack
    # duel
    # dice

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