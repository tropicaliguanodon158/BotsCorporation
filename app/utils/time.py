from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


# ============================================================================
# DEFAULTS
# ============================================================================

DEFAULT_TIMEZONE = "Europe/Warsaw"


# ============================================================================
# TIMEZONE
# ============================================================================


def get_timezone(
    timezone_name: str | None = None,
) -> ZoneInfo:
    """
    Возвращает объект часового пояса.

    Если timezone_name не указан или некорректен,
    используется DEFAULT_TIMEZONE.
    """

    if not timezone_name:
        timezone_name = DEFAULT_TIMEZONE

    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo(DEFAULT_TIMEZONE)


# ============================================================================
# CURRENT TIME
# ============================================================================


def utc_now() -> datetime:
    """
    Текущее время UTC.

    Все timestamps в базе желательно хранить в UTC.
    """

    return datetime.now(timezone.utc)


def now(
    timezone_name: str | None = None,
) -> datetime:
    """
    Текущее время в указанном часовом поясе.

    Пример:

        now("Europe/Warsaw")
    """

    tz = get_timezone(timezone_name)

    return datetime.now(tz)


# ============================================================================
# DATETIME NORMALIZATION
# ============================================================================


def ensure_aware(
    value: datetime,
    timezone_name: str | None = None,
) -> datetime:
    """
    Делает datetime timezone-aware.

    Если timezone уже указан — значение не изменяется.

    Если timezone отсутствует, предполагается timezone_name.
    """

    if value.tzinfo is not None:
        return value

    tz = get_timezone(timezone_name)

    return value.replace(tzinfo=tz)


def to_utc(
    value: datetime,
    timezone_name: str | None = None,
) -> datetime:
    """
    Переводит datetime в UTC.
    """

    value = ensure_aware(
        value,
        timezone_name,
    )

    return value.astimezone(
        timezone.utc
    )


def to_timezone(
    value: datetime,
    timezone_name: str | None = None,
) -> datetime:
    """
    Переводит datetime в нужный часовой пояс.
    """

    value = ensure_aware(
        value,
        timezone_name,
    )

    return value.astimezone(
        get_timezone(timezone_name)
    )


# ============================================================================
# DAY
# ============================================================================


def start_of_day(
    value: datetime | None = None,
    timezone_name: str | None = None,
) -> datetime:
    """
    Начало дня в указанном часовом поясе.

    Например:

        2026-08-17 00:00:00
    """

    if value is None:
        value = now(timezone_name)
    else:
        value = to_timezone(
            value,
            timezone_name,
        )

    return value.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def end_of_day(
    value: datetime | None = None,
    timezone_name: str | None = None,
) -> datetime:
    """
    Конец дня.

    Возвращает:

        23:59:59.999999
    """

    start = start_of_day(
        value,
        timezone_name,
    )

    return start + timedelta(
        days=1,
        microseconds=-1,
    )


def start_of_next_day(
    value: datetime | None = None,
    timezone_name: str | None = None,
) -> datetime:
    """
    Начало следующего дня.
    """

    return start_of_day(
        value,
        timezone_name,
    ) + timedelta(days=1)


# ============================================================================
# DAY COMPARISON
# ============================================================================


def is_same_day(
    first: datetime,
    second: datetime,
    timezone_name: str | None = None,
) -> bool:
    """
    Проверяет, относятся ли два datetime к одному
    календарному дню в указанном часовом поясе.
    """

    first_local = to_timezone(
        first,
        timezone_name,
    )

    second_local = to_timezone(
        second,
        timezone_name,
    )

    return (
        first_local.date()
        == second_local.date()
    )


def is_today(
    value: datetime,
    timezone_name: str | None = None,
) -> bool:
    """
    Проверяет, является ли дата сегодняшней.
    """

    return is_same_day(
        value,
        now(timezone_name),
        timezone_name,
    )


# ============================================================================
# TOMORROW / YESTERDAY
# ============================================================================


def yesterday(
    timezone_name: str | None = None,
) -> datetime:
    """
    Текущее время минус один день.
    """

    return now(timezone_name) - timedelta(
        days=1
    )


def tomorrow(
    timezone_name: str | None = None,
) -> datetime:
    """
    Текущее время плюс один день.
    """

    return now(timezone_name) + timedelta(
        days=1
    )


# ============================================================================
# DURATION
# ============================================================================


def add_seconds(
    value: datetime,
    seconds: int | float,
) -> datetime:
    """
    Добавляет секунды к datetime.
    """

    return value + timedelta(
        seconds=seconds
    )


def add_minutes(
    value: datetime,
    minutes: int | float,
) -> datetime:
    """
    Добавляет минуты к datetime.
    """

    return value + timedelta(
        minutes=minutes
    )


def add_hours(
    value: datetime,
    hours: int | float,
) -> datetime:
    """
    Добавляет часы к datetime.
    """

    return value + timedelta(
        hours=hours
    )


def add_days(
    value: datetime,
    days: int | float,
) -> datetime:
    """
    Добавляет дни к datetime.
    """

    return value + timedelta(
        days=days
    )


# ============================================================================
# EXPIRATION
# ============================================================================


def is_expired(
    expires_at: datetime | None,
    current_time: datetime | None = None,
) -> bool:
    """
    Проверяет, истёк ли срок действия.

    None означает отсутствие срока,
    поэтому такой объект считается неистёкшим.
    """

    if expires_at is None:
        return False

    if current_time is None:
        current_time = utc_now()

    expires_at = ensure_aware(
        expires_at
    )

    current_time = ensure_aware(
        current_time
    )

    return current_time >= expires_at


def seconds_until(
    target: datetime,
    current_time: datetime | None = None,
) -> int:
    """
    Возвращает количество секунд до указанного времени.

    Если время уже прошло — возвращает 0.
    """

    if current_time is None:
        current_time = utc_now()

    target = ensure_aware(target)
    current_time = ensure_aware(current_time)

    seconds = (
        target - current_time
    ).total_seconds()

    return max(
        0,
        int(seconds),
    )


def minutes_until(
    target: datetime,
    current_time: datetime | None = None,
) -> int:
    """
    Возвращает количество минут до указанного времени.
    """

    seconds = seconds_until(
        target,
        current_time,
    )

    return seconds // 60


# ============================================================================
# COOLDOWNS
# ============================================================================


def cooldown_until(
    seconds: int | float,
    from_time: datetime | None = None,
) -> datetime:
    """
    Создаёт timestamp окончания cooldown.

    Например:

        cooldown_until(3600)

    -> текущее время + 1 час.
    """

    if from_time is None:
        from_time = utc_now()

    return add_seconds(
        from_time,
        seconds,
    )


def cooldown_active(
    cooldown_until_value: datetime | None,
    current_time: datetime | None = None,
) -> bool:
    """
    Проверяет, активен ли cooldown.
    """

    if cooldown_until_value is None:
        return False

    return not is_expired(
        cooldown_until_value,
        current_time,
    )


# ============================================================================
# DAILY RESET
# ============================================================================


def seconds_until_next_day(
    timezone_name: str | None = None,
) -> int:
    """
    Сколько секунд осталось до начала следующего дня.
    """

    current = now(timezone_name)

    next_day = start_of_next_day(
        current,
        timezone_name,
    )

    return max(
        0,
        int(
            (
                next_day - current
            ).total_seconds()
        ),
    )


def should_reset_daily_counter(
    last_reset_at: datetime | None,
    timezone_name: str | None = None,
) -> bool:
    """
    Определяет, нужно ли сбросить суточный счётчик.

    Используется для:

        daily_message_count
        ежедневных наград
        дневных квестов
        условий пассивного фарма
        дневных лимитов
    """

    if last_reset_at is None:
        return True

    return not is_today(
        last_reset_at,
        timezone_name,
    )


# ============================================================================
# DAILY ACTIVITY
# ============================================================================


def daily_requirement_met(
    current_count: int,
    required_count: int,
) -> bool:
    """
    Проверяет выполнение дневного требования.

    Например:

        30 сообщений за день.
    """

    return current_count >= required_count


def remaining_daily_requirement(
    current_count: int,
    required_count: int,
) -> int:
    """
    Возвращает, сколько ещё нужно выполнить
    до дневного требования.

    Пример:

        17 из 30 -> 13
    """

    return max(
        0,
        required_count - current_count,
    )


# ============================================================================
# PERIOD CHECKS
# ============================================================================


def is_within_period(
    value: datetime,
    start: datetime,
    end: datetime,
) -> bool:
    """
    Проверяет, находится ли datetime внутри периода.

    Границы включаются.
    """

    value = ensure_aware(value)
    start = ensure_aware(start)
    end = ensure_aware(end)

    return start <= value <= end


# ============================================================================
# UNIX TIMESTAMP
# ============================================================================


def to_timestamp(
    value: datetime,
) -> int:
    """
    Переводит datetime в Unix timestamp.
    """

    value = ensure_aware(value)

    return int(
        value.timestamp()
    )


def from_timestamp(
    timestamp: int | float,
    timezone_name: str | None = None,
) -> datetime:
    """
    Создаёт datetime из Unix timestamp.

    По умолчанию возвращает UTC.
    Если указан timezone_name —
    переводит в него.
    """

    value = datetime.fromtimestamp(
        timestamp,
        timezone.utc,
    )

    if timezone_name:
        return value.astimezone(
            get_timezone(timezone_name)
        )

    return value


# ============================================================================
# DATE KEYS
# ============================================================================


def date_key(
    value: datetime | None = None,
    timezone_name: str | None = None,
) -> str:
    """
    Возвращает стабильный ключ календарного дня.

    Например:

        "2026-08-17"

    Такой ключ удобно использовать в settings_json,
    статистике и ежедневных событиях.
    """

    if value is None:
        value = now(timezone_name)

    value = to_timezone(
        value,
        timezone_name,
    )

    return value.strftime(
        "%Y-%m-%d"
    )


# ============================================================================
# WEEK
# ============================================================================


def start_of_week(
    value: datetime | None = None,
    timezone_name: str | None = None,
) -> datetime:
    """
    Начало недели — понедельник 00:00.
    """

    if value is None:
        value = now(timezone_name)
    else:
        value = to_timezone(
            value,
            timezone_name,
        )

    day_start = value.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    return day_start - timedelta(
        days=day_start.weekday()
    )


def end_of_week(
    value: datetime | None = None,
    timezone_name: str | None = None,
) -> datetime:
    """
    Конец недели — воскресенье 23:59:59.999999.
    """

    return (
        start_of_week(
            value,
            timezone_name,
        )
        + timedelta(days=7)
        - timedelta(microseconds=1)
    )


# ============================================================================
# MONTH
# ============================================================================


def start_of_month(
    value: datetime | None = None,
    timezone_name: str | None = None,
) -> datetime:
    """
    Начало текущего месяца.
    """

    if value is None:
        value = now(timezone_name)
    else:
        value = to_timezone(
            value,
            timezone_name,
        )

    return value.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def is_same_month(
    first: datetime,
    second: datetime,
    timezone_name: str | None = None,
) -> bool:
    """
    Проверяет, находятся ли даты в одном месяце.
    """

    first = to_timezone(
        first,
        timezone_name,
    )

    second = to_timezone(
        second,
        timezone_name,
    )

    return (
        first.year == second.year
        and first.month == second.month
    )