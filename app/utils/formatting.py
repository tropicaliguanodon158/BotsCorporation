from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP


# ============================================================================
# NUMBERS
# ============================================================================


def format_number(
    value: int | float | Decimal,
) -> str:
    """
    Форматирует число с разделителями тысяч.

    Примеры:

        1000      -> "1 000"
        1500000   -> "1 500 000"
        1234.56   -> "1 234.56"
    """

    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return f"{int(value):,}".replace(",", " ")

        return f"{value:,.2f}".replace(",", " ")

    if isinstance(value, int):
        return f"{value:,}".replace(",", " ")

    return f"{value:,.2f}".replace(",", " ")


def format_decimal(
    value: Decimal | int | float,
    decimals: int = 2,
) -> str:
    """
    Форматирует Decimal с заданным количеством знаков.

    Пример:

        format_decimal(1234.5)
        -> "1 234.50"
    """

    if decimals < 0:
        raise ValueError(
            "decimals не может быть отрицательным."
        )

    decimal_value = Decimal(str(value))

    quantizer = Decimal(
        "1." + ("0" * decimals)
    )

    decimal_value = decimal_value.quantize(
        quantizer,
        rounding=ROUND_HALF_UP,
    )

    formatted = f"{decimal_value:,.{decimals}f}"

    return formatted.replace(",", " ")


# ============================================================================
# CURRENCY
# ============================================================================


def format_currency(
    amount: Decimal | int | float,
    currency_name: str = "монет",
    currency_symbol: str = "🪙",
    decimals: int = 2,
) -> str:
    """
    Форматирует денежную сумму.

    Пример:

        format_currency(
            1250,
            "монет",
            "🪙",
        )

        -> "🪙 1 250.00 монет"
    """

    formatted_amount = format_decimal(
        amount,
        decimals=decimals,
    )

    return (
        f"{currency_symbol} "
        f"{formatted_amount} "
        f"{currency_name}"
    )


def format_balance(
    amount: Decimal | int | float,
    currency_symbol: str = "🪙",
) -> str:
    """
    Короткое отображение баланса.

    Пример:

        "🪙 1 250.00"
    """

    return (
        f"{currency_symbol} "
        f"{format_decimal(amount)}"
    )


# ============================================================================
# PERCENT
# ============================================================================


def format_percent(
    value: float | Decimal,
    decimals: int = 1,
) -> str:
    """
    Форматирует процент.

    Пример:

        15 -> "15.0%"
    """

    return (
        f"{float(value):.{decimals}f}%"
    )


# ============================================================================
# SIGNED NUMBERS
# ============================================================================


def format_signed(
    value: int | float | Decimal,
) -> str:
    """
    Форматирует число со знаком.

    Примеры:

        +15
        -10
        0
    """

    if isinstance(value, Decimal):
        if value > 0:
            return f"+{value}"
        return str(value)

    if value > 0:
        return f"+{value}"

    return str(value)


# ============================================================================
# DURATION
# ============================================================================


def format_duration(
    seconds: int | float,
) -> str:
    """
    Форматирует длительность в удобный вид.

    Примеры:

        5        -> "5 сек."
        65       -> "1 мин. 5 сек."
        3665     -> "1 ч. 1 мин. 5 сек."
        90000    -> "1 д. 1 ч."
    """

    total_seconds = max(
        0,
        int(seconds),
    )

    days, remainder = divmod(
        total_seconds,
        86400,
    )

    hours, remainder = divmod(
        remainder,
        3600,
    )

    minutes, seconds = divmod(
        remainder,
        60,
    )

    parts: list[str] = []

    if days:
        parts.append(
            f"{days} д."
        )

    if hours:
        parts.append(
            f"{hours} ч."
        )

    if minutes:
        parts.append(
            f"{minutes} мин."
        )

    if seconds or not parts:
        parts.append(
            f"{seconds} сек."
        )

    return " ".join(parts)


def format_timedelta(
    value: timedelta,
) -> str:
    """
    Форматирует timedelta.
    """

    return format_duration(
        value.total_seconds()
    )


# ============================================================================
# DATETIME
# ============================================================================


def format_datetime(
    value: datetime | None,
    format_string: str = "%d.%m.%Y %H:%M",
) -> str:
    """
    Форматирует datetime.

    None -> "—"
    """

    if value is None:
        return "—"

    return value.strftime(
        format_string
    )


def format_date(
    value: datetime | None,
) -> str:
    """
    Форматирует только дату.
    """

    return format_datetime(
        value,
        "%d.%m.%Y",
    )


def format_time(
    value: datetime | None,
) -> str:
    """
    Форматирует только время.
    """

    return format_datetime(
        value,
        "%H:%M:%S",
    )


# ============================================================================
# COOLDOWN
# ============================================================================


def format_cooldown(
    seconds: int | float,
) -> str:
    """
    Форматирует оставшееся время cooldown.

    Удобно использовать прямо в сообщении:

        "Попробуй снова через 14 мин. 32 сек."
    """

    return format_duration(
        max(0, seconds)
    )


# ============================================================================
# XP / LEVEL
# ============================================================================


def format_xp(
    current_xp: int,
    required_xp: int,
) -> str:
    """
    Форматирует прогресс опыта.

    Пример:

        "750 / 1000 XP"
    """

    return (
        f"{format_number(current_xp)} / "
        f"{format_number(required_xp)} XP"
    )


def format_level(
    level: int,
) -> str:
    """
    Форматирует уровень персонажа/пользователя.
    """

    return f"Уровень {level}"


# ============================================================================
# HP / STATS
# ============================================================================


def format_hp(
    hp: int,
    max_hp: int,
) -> str:
    """
    Форматирует здоровье.

    Пример:

        "❤️ 85 / 100"
    """

    return (
        f"❤️ {format_number(hp)} / "
        f"{format_number(max_hp)}"
    )


def format_stat(
    name: str,
    value: int,
) -> str:
    """
    Форматирует одну характеристику.

    Пример:

        format_stat("Сила", 25)
        -> "💪 Сила: 25"
    """

    return (
        f"{name}: "
        f"{format_number(value)}"
    )


# ============================================================================
# PROGRESS BAR
# ============================================================================


def progress_bar(
    current: int | float,
    maximum: int | float,
    length: int = 10,
    filled: str = "█",
    empty: str = "░",
) -> str:
    """
    Создаёт текстовый progress bar.

    Пример:

        ███████░░░
    """

    if length <= 0:
        raise ValueError(
            "length должен быть больше нуля."
        )

    if maximum <= 0:
        ratio = 0.0
    else:
        ratio = current / maximum

    ratio = max(
        0.0,
        min(1.0, ratio),
    )

    filled_count = round(
        ratio * length
    )

    empty_count = (
        length - filled_count
    )

    return (
        filled * filled_count
        + empty * empty_count
    )


def format_progress(
    current: int | float,
    maximum: int | float,
    length: int = 10,
) -> str:
    """
    Форматирует progress bar вместе с числовым значением.

    Пример:

        ███████░░░ 750 / 1000
    """

    return (
        f"{progress_bar(current, maximum, length)} "
        f"{format_number(current)} / "
        f"{format_number(maximum)}"
    )


# ============================================================================
# USERNAME / DISPLAY NAME
# ============================================================================


def format_user_name(
    first_name: str | None = None,
    last_name: str | None = None,
    username: str | None = None,
) -> str:
    """
    Возвращает наиболее подходящее отображаемое имя пользователя.

    Приоритет:

        1. first_name + last_name
        2. first_name
        3. @username
        4. "Пользователь"
    """

    parts: list[str] = []

    if first_name:
        parts.append(
            first_name.strip()
        )

    if last_name:
        parts.append(
            last_name.strip()
        )

    if parts:
        return " ".join(parts)

    if username:
        username = username.strip()

        if not username.startswith("@"):
            username = f"@{username}"

        return username

    return "Пользователь"


# ============================================================================
# TRUNCATION
# ============================================================================


def truncate(
    text: str,
    max_length: int,
    suffix: str = "...",
) -> str:
    """
    Обрезает длинный текст.

    Используется для:
        - bio;
        - названий;
        - описаний;
        - логов;
        - сообщений Founder Panel.
    """

    if max_length <= 0:
        raise ValueError(
            "max_length должен быть больше нуля."
        )

    if len(text) <= max_length:
        return text

    if len(suffix) >= max_length:
        return suffix[:max_length]

    return (
        text[
            : max_length - len(suffix)
        ]
        + suffix
    )


# ============================================================================
# ESCAPING
# ============================================================================


def escape_html(
    text: str,
) -> str:
    """
    Экранирует HTML-символы.

    Нужен при формировании сообщений Telegram
    с parse_mode=HTML.
    """

    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def escape_markdown_v2(
    text: str,
) -> str:
    """
    Экранирует специальные символы Telegram MarkdownV2.
    """

    special_chars = (
        "_*[]()~`>#+-=|{}.!\\"
    )

    result = text

    for char in special_chars:
        result = result.replace(
            char,
            f"\\{char}",
        )

    return result