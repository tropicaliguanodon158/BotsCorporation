from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
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
# USER DAILY ACTIVITY
# ============================================================================


class UserDailyActivity(Base):
    """
    Ежедневная статистика активности пользователя.

    Используется для:
        - ежедневных наград;
        - пассивного фарма;
        - заданий;
        - анти-абуза;
        - статистики.
    """

    __tablename__ = "user_daily_activity"

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

    activity_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    messages_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    text_messages: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    photo_messages: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    video_messages: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    other_messages: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Economy activity
    # ------------------------------------------------------------------

    earned_currency: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    spent_currency: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Daily rewards
    # ------------------------------------------------------------------

    daily_reward_claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Activity flags
    # ------------------------------------------------------------------

    active_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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
            "activity_date",
            name="uq_user_daily_activity",
        ),
    )


# ============================================================================
# TASK DEFINITIONS
# ============================================================================


class Task(Base):
    """
    Определение задания.

    Задания можно создавать через Founder Panel.

    Примеры:

        Написать 30 сообщений
        Открыть 3 кейса
        Выиграть 5 дуэлей
        Использовать способность 10 раз
    """

    __tablename__ = "tasks"

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

    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    target_value: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    reward_currency: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    reward_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    reward_gems: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    reward_item_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("items.id", ondelete="SET NULL"),
        nullable=True,
    )

    task_period: Mapped[str] = mapped_column(
        String(30),
        default="daily",
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
# USER TASK PROGRESS
# ============================================================================


class UserTask(Base):
    """
    Прогресс конкретного пользователя по заданию.
    """

    __tablename__ = "user_tasks"

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

    task_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    period_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
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
# ACHIEVEMENTS
# ============================================================================


class Achievement(Base):
    """
    Долгосрочное достижение.
    """

    __tablename__ = "achievements"

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

    condition_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    condition_value: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    reward_currency: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    reward_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    reward_gems: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    reward_item_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("items.id", ondelete="SET NULL"),
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


# ============================================================================
# USER ACHIEVEMENTS
# ============================================================================


class UserAchievement(Base):
    """
    Полученное пользователем достижение.
    """

    __tablename__ = "user_achievements"

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

    achievement_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("achievements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "achievement_id",
            name="uq_user_achievement",
        ),
    )