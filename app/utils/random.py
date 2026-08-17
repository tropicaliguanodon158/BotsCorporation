from __future__ import annotations

import secrets
from decimal import Decimal
from typing import Sequence, TypeVar


T = TypeVar("T")


# ============================================================================
# BASIC RANDOM
# ============================================================================


def randint(
    minimum: int,
    maximum: int,
) -> int:
    """
    Возвращает случайное целое число
    в диапазоне [minimum, maximum].

    Использует криптографически стойкий генератор
    secrets вместо обычного random.
    """

    if minimum > maximum:
        raise ValueError(
            "minimum не может быть больше maximum."
        )

    return secrets.randbelow(
        maximum - minimum + 1
    ) + minimum


def random_float(
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    """
    Возвращает случайное число с плавающей точкой
    в диапазоне [minimum, maximum).
    """

    if minimum > maximum:
        raise ValueError(
            "minimum не может быть больше maximum."
        )

    if minimum == maximum:
        return minimum

    # Получаем большое случайное целое
    # и нормализуем его в диапазон 0..1.
    value = secrets.randbits(53) / (2**53)

    return minimum + (
        (maximum - minimum) * value
    )


# ============================================================================
# CHOICE
# ============================================================================


def choice(
    items: Sequence[T],
) -> T:
    """
    Возвращает случайный элемент последовательности.
    """

    if not items:
        raise ValueError(
            "Нельзя выбрать элемент из пустой последовательности."
        )

    return items[
        secrets.randbelow(len(items))
    ]


# ============================================================================
# BOOLEAN / COIN
# ============================================================================


def coinflip() -> bool:
    """
    Подбрасывает монетку.

    True  = орёл
    False = решка
    """

    return bool(
        secrets.randbelow(2)
    )


# ============================================================================
# CHANCE
# ============================================================================


def chance(
    probability: float,
) -> bool:
    """
    Проверяет вероятность события.

    probability:
        значение от 0.0 до 1.0.

    Например:

        chance(0.5) -> 50%
        chance(0.1) -> 10%
        chance(1.0) -> 100%
        chance(0.0) -> 0%
    """

    if not 0.0 <= probability <= 1.0:
        raise ValueError(
            "probability должна находиться "
            "в диапазоне от 0.0 до 1.0."
        )

    if probability == 0.0:
        return False

    if probability == 1.0:
        return True

    return random_float() < probability


def chance_percent(
    percent: float,
) -> bool:
    """
    Версия chance() с процентами.

    Например:

        chance_percent(50) -> 50%
        chance_percent(25) -> 25%
        chance_percent(1)  -> 1%
    """

    if not 0.0 <= percent <= 100.0:
        raise ValueError(
            "percent должен находиться "
            "в диапазоне от 0 до 100."
        )

    return chance(
        percent / 100.0
    )


# ============================================================================
# WEIGHTED CHOICE
# ============================================================================


def weighted_choice(
    items: Sequence[tuple[T, float]],
) -> T:
    """
    Выбирает элемент с учётом веса.

    Пример:

        weighted_choice(
            [
                ("common", 70),
                ("rare", 25),
                ("legendary", 5),
            ]
        )

    Чем больше weight, тем выше вероятность.

    Вес не обязан суммироваться до 100.
    """

    if not items:
        raise ValueError(
            "Нельзя выбрать элемент из пустого списка."
        )

    total_weight = 0.0

    for _, weight in items:
        if weight < 0:
            raise ValueError(
                "Вес не может быть отрицательным."
            )

        total_weight += weight

    if total_weight <= 0:
        raise ValueError(
            "Суммарный вес должен быть больше нуля."
        )

    target = random_float(
        0.0,
        total_weight,
    )

    current = 0.0

    for item, weight in items:
        current += weight

        if target < current:
            return item

    # Защита от погрешности float.
    return items[-1][0]


# ============================================================================
# RANDOM DECIMAL
# ============================================================================


def random_decimal(
    minimum: Decimal,
    maximum: Decimal,
    decimals: int = 2,
) -> Decimal:
    """
    Возвращает случайное Decimal-значение
    с заданным количеством знаков после запятой.

    Используется для экономики, когда нужно получить
    случайную денежную сумму.
    """

    if minimum > maximum:
        raise ValueError(
            "minimum не может быть больше maximum."
        )

    if decimals < 0:
        raise ValueError(
            "decimals не может быть отрицательным."
        )

    multiplier = 10 ** decimals

    minimum_int = int(
        minimum * multiplier
    )

    maximum_int = int(
        maximum * multiplier
    )

    value = randint(
        minimum_int,
        maximum_int,
    )

    return Decimal(value) / Decimal(
        multiplier
    )


# ============================================================================
# RANDOM RANGE
# ============================================================================


def random_range(
    minimum: int,
    maximum: int,
    count: int,
) -> list[int]:
    """
    Возвращает count случайных уникальных чисел
    в указанном диапазоне.

    Используется, например, для некоторых игровых механик.
    """

    if minimum > maximum:
        raise ValueError(
            "minimum не может быть больше maximum."
        )

    available = maximum - minimum + 1

    if count < 0:
        raise ValueError(
            "count не может быть отрицательным."
        )

    if count > available:
        raise ValueError(
            "Нельзя получить больше уникальных чисел, "
            "чем существует в диапазоне."
        )

    numbers = list(
        range(
            minimum,
            maximum + 1,
        )
    )

    # Перемешиваем вручную через secrets.
    #
    # Fisher-Yates.
    for index in range(
        len(numbers) - 1,
        0,
        -1,
    ):
        swap_index = secrets.randbelow(
            index + 1
        )

        numbers[index], numbers[swap_index] = (
            numbers[swap_index],
            numbers[index],
        )

    return numbers[:count]


# ============================================================================
# ROULETTE
# ============================================================================


def roulette_number() -> int:
    """
    Генерирует число европейской рулетки.

    Диапазон:

        0..36
    """

    return randint(0, 36)


def roulette_color(
    number: int,
) -> str:
    """
    Возвращает цвет числа европейской рулетки.

    Возможные значения:

        green
        red
        black
    """

    if not 0 <= number <= 36:
        raise ValueError(
            "Номер рулетки должен находиться "
            "в диапазоне 0..36."
        )

    if number == 0:
        return "green"

    red_numbers = {
        1, 3, 5, 7, 9,
        12, 14, 16, 18,
        19, 21, 23, 25,
        27, 30, 32, 34, 36,
    }

    if number in red_numbers:
        return "red"

    return "black"


# ============================================================================
# DICE
# ============================================================================


def roll_dice(
    sides: int = 6,
) -> int:
    """
    Бросает игровой кубик.

    Например:

        roll_dice()      -> 1..6
        roll_dice(20)    -> 1..20
        roll_dice(100)   -> 1..100
    """

    if sides < 2:
        raise ValueError(
            "У кубика должно быть минимум 2 грани."
        )

    return randint(
        1,
        sides,
    )


def roll_dice_multiple(
    count: int,
    sides: int = 6,
) -> list[int]:
    """
    Бросает несколько кубиков.
    """

    if count < 1:
        raise ValueError(
            "Количество кубиков должно быть больше нуля."
        )

    return [
        roll_dice(sides)
        for _ in range(count)
    ]


# ============================================================================
# SHUFFLE
# ============================================================================


def shuffle(
    items: Sequence[T],
) -> list[T]:
    """
    Возвращает новую перемешанную копию последовательности.

    Исходный объект не изменяется.
    """

    result = list(items)

    for index in range(
        len(result) - 1,
        0,
        -1,
    ):
        swap_index = secrets.randbelow(
            index + 1
        )

        result[index], result[swap_index] = (
            result[swap_index],
            result[index],
        )

    return result