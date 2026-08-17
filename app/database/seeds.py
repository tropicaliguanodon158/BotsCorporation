from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    Ability,
    AdminLevel,
    Case,
    CaseReward,
    CharacterRank,
    InteractionType,
    Item,
    Race,
)


# ============================================================================
# DEFAULT RACES
# ============================================================================

DEFAULT_RACES = (
    {
        "name": "Человек",
        "description": "Универсальная раса без ярко выраженных слабостей.",
        "base_hp": 100,
        "base_strength": 10,
        "base_defense": 10,
        "base_luck": 10,
        "base_speed": 10,
        "base_intelligence": 10,
    },
    {
        "name": "Эльф",
        "description": "Быстрый и умный народ.",
        "base_hp": 90,
        "base_strength": 9,
        "base_defense": 8,
        "base_luck": 14,
        "base_speed": 15,
        "base_intelligence": 16,
    },
    {
        "name": "Орк",
        "description": "Сильная и выносливая раса.",
        "base_hp": 140,
        "base_strength": 16,
        "base_defense": 13,
        "base_luck": 6,
        "base_speed": 7,
        "base_intelligence": 6,
    },
    {
        "name": "Гном",
        "description": "Выносливый народ мастеров.",
        "base_hp": 120,
        "base_strength": 12,
        "base_defense": 15,
        "base_luck": 11,
        "base_speed": 6,
        "base_intelligence": 13,
    },
    {
        "name": "Демон",
        "description": "Опасная раса с высоким потенциалом.",
        "base_hp": 115,
        "base_strength": 15,
        "base_defense": 10,
        "base_luck": 13,
        "base_speed": 12,
        "base_intelligence": 15,
    },
)


# ============================================================================
# DEFAULT RANKS
# ============================================================================

DEFAULT_RANKS = (
    {
        "name": "Новобранец",
        "level": 1,
        "description": "Начальный ранг.",
        "required_level": 1,
        "required_xp": 0,
        "required_reputation": 0,
        "hp_bonus": 0,
        "strength_bonus": 0,
        "defense_bonus": 0,
        "luck_bonus": 0,
        "speed_bonus": 0,
        "intelligence_bonus": 0,
    },
    {
        "name": "Искатель",
        "level": 2,
        "description": "Первое серьёзное продвижение.",
        "required_level": 5,
        "required_xp": 500,
        "required_reputation": 0,
        "hp_bonus": 5,
        "strength_bonus": 1,
        "defense_bonus": 1,
        "luck_bonus": 1,
        "speed_bonus": 1,
        "intelligence_bonus": 1,
    },
    {
        "name": "Воин",
        "level": 3,
        "description": "Опытный игрок.",
        "required_level": 10,
        "required_xp": 1500,
        "required_reputation": 5,
        "hp_bonus": 10,
        "strength_bonus": 3,
        "defense_bonus": 2,
        "luck_bonus": 2,
        "speed_bonus": 2,
        "intelligence_bonus": 2,
    },
    {
        "name": "Ветеран",
        "level": 4,
        "description": "Проверенный временем игрок.",
        "required_level": 20,
        "required_xp": 5000,
        "required_reputation": 15,
        "hp_bonus": 20,
        "strength_bonus": 5,
        "defense_bonus": 5,
        "luck_bonus": 3,
        "speed_bonus": 3,
        "intelligence_bonus": 3,
    },
    {
        "name": "Элита",
        "level": 5,
        "description": "Высшая игровая элита.",
        "required_level": 35,
        "required_xp": 15000,
        "required_reputation": 30,
        "hp_bonus": 35,
        "strength_bonus": 8,
        "defense_bonus": 8,
        "luck_bonus": 5,
        "speed_bonus": 5,
        "intelligence_bonus": 5,
    },
    {
        "name": "Легенда",
        "level": 6,
        "description": "Легендарный игрок.",
        "required_level": 50,
        "required_xp": 40000,
        "required_reputation": 50,
        "hp_bonus": 60,
        "strength_bonus": 12,
        "defense_bonus": 12,
        "luck_bonus": 8,
        "speed_bonus": 8,
        "intelligence_bonus": 8,
    },
)


# ============================================================================
# DEFAULT ABILITIES
# ============================================================================

DEFAULT_ABILITIES = (
    {
        "name": "Берсерк",
        "description": "Увеличивает силу персонажа.",
        "ability_type": "strength",
        "effect_value": 10,
        "duration_seconds": 60,
        "cooldown_seconds": 300,
    },
    {
        "name": "Железная кожа",
        "description": "Увеличивает защиту персонажа.",
        "ability_type": "defense",
        "effect_value": 10,
        "duration_seconds": 60,
        "cooldown_seconds": 300,
    },
    {
        "name": "Удачливый",
        "description": "Увеличивает удачу.",
        "ability_type": "luck",
        "effect_value": 10,
        "duration_seconds": 120,
        "cooldown_seconds": 300,
    },
    {
        "name": "Стремительность",
        "description": "Увеличивает скорость.",
        "ability_type": "speed",
        "effect_value": 10,
        "duration_seconds": 60,
        "cooldown_seconds": 300,
    },
    {
        "name": "Регенерация",
        "description": "Восстанавливает здоровье.",
        "ability_type": "heal",
        "effect_value": 25,
        "duration_seconds": 0,
        "cooldown_seconds": 600,
    },
)


# ============================================================================
# DEFAULT ITEMS
# ============================================================================

DEFAULT_ITEMS = (
    {
        "name": "Зелье здоровья",
        "description": "Восстанавливает здоровье.",
        "item_type": "consumable",
        "rarity": "common",
        "price": Decimal("100.00"),
        "effect_type": "heal",
        "effect_value": 25,
    },
    {
        "name": "Эликсир силы",
        "description": "Временное усиление силы.",
        "item_type": "consumable",
        "rarity": "rare",
        "price": Decimal("500.00"),
        "effect_type": "strength",
        "effect_value": 10,
        "effect_duration_seconds": 3600,
    },
    {
        "name": "Кристалл удачи",
        "description": "Редкий магический предмет.",
        "item_type": "accessory",
        "rarity": "epic",
        "price": Decimal("1500.00"),
        "luck_bonus": 5,
    },
)


# ============================================================================
# DEFAULT CASES
# ============================================================================

DEFAULT_CASES = (
    {
        "name": "Обычный кейс",
        "description": "Небольшой набор случайных наград.",
        "price": Decimal("250.00"),
        "currency_type": "currency",
        "rewards": (
            {
                "reward_type": "currency",
                "min_amount": Decimal("100"),
                "max_amount": Decimal("300"),
                "probability": Decimal("70"),
                "display_name": "🪙 100–300 монет",
                "rarity": "common",
            },
            {
                "reward_type": "gems",
                "min_amount": Decimal("1"),
                "max_amount": Decimal("3"),
                "probability": Decimal("20"),
                "display_name": "💎 1–3 гемов",
                "rarity": "rare",
            },
            {
                "reward_type": "xp",
                "min_amount": Decimal("100"),
                "max_amount": Decimal("250"),
                "probability": Decimal("9"),
                "display_name": "⭐ 100–250 XP",
                "rarity": "epic",
            },
            {
                "reward_type": "currency",
                "min_amount": Decimal("1000"),
                "max_amount": Decimal("1000"),
                "probability": Decimal("1"),
                "display_name": "🔥 1000 монет",
                "rarity": "legendary",
            },
        ),
    },
    {
        "name": "Редкий кейс",
        "description": "Кейс с более ценными наградами.",
        "price": Decimal("750.00"),
        "currency_type": "currency",
        "rewards": (
            {
                "reward_type": "currency",
                "min_amount": Decimal("400"),
                "max_amount": Decimal("800"),
                "probability": Decimal("65"),
                "display_name": "🪙 400–800 монет",
                "rarity": "common",
            },
            {
                "reward_type": "gems",
                "min_amount": Decimal("3"),
                "max_amount": Decimal("7"),
                "probability": Decimal("25"),
                "display_name": "💎 3–7 гемов",
                "rarity": "rare",
            },
            {
                "reward_type": "xp",
                "min_amount": Decimal("500"),
                "max_amount": Decimal("1000"),
                "probability": Decimal("9"),
                "display_name": "⭐ 500–1000 XP",
                "rarity": "epic",
            },
            {
                "reward_type": "gems",
                "min_amount": Decimal("25"),
                "max_amount": Decimal("25"),
                "probability": Decimal("1"),
                "display_name": "💎 25 гемов",
                "rarity": "legendary",
            },
        ),
    },
    {
        "name": "Эпический кейс",
        "description": "Очень ценный набор наград.",
        "price": Decimal("2500.00"),
        "currency_type": "currency",
        "rewards": (
            {
                "reward_type": "currency",
                "min_amount": Decimal("1500"),
                "max_amount": Decimal("3000"),
                "probability": Decimal("60"),
                "display_name": "🪙 1500–3000 монет",
                "rarity": "common",
            },
            {
                "reward_type": "gems",
                "min_amount": Decimal("10"),
                "max_amount": Decimal("20"),
                "probability": Decimal("30"),
                "display_name": "💎 10–20 гемов",
                "rarity": "rare",
            },
            {
                "reward_type": "xp",
                "min_amount": Decimal("2000"),
                "max_amount": Decimal("4000"),
                "probability": Decimal("9"),
                "display_name": "⭐ 2000–4000 XP",
                "rarity": "epic",
            },
            {
                "reward_type": "gems",
                "min_amount": Decimal("100"),
                "max_amount": Decimal("100"),
                "probability": Decimal("1"),
                "display_name": "💎 100 гемов",
                "rarity": "legendary",
            },
        ),
    },
)


# ============================================================================
# DEFAULT INTERACTIONS
# ============================================================================

DEFAULT_INTERACTIONS = (
    {
        "command": "hit",
        "name": "Ударить",
        "description": "Ударить другого игрока.",
        "cost": Decimal("10"),
        "success_text": "🥊 <b>{actor}</b> ударил <b>{target}</b>!",
        "effect_type": "damage",
        "effect_value": 10,
    },
    {
        "command": "kiss",
        "name": "Поцеловать",
        "description": "Поцеловать другого игрока.",
        "cost": Decimal("5"),
        "success_text": "💋 <b>{actor}</b> поцеловал <b>{target}</b>!",
        "effect_type": "none",
    },
    {
        "command": "hug",
        "name": "Обнять",
        "description": "Обнять другого игрока.",
        "cost": Decimal("3"),
        "success_text": "🤗 <b>{actor}</b> обнял <b>{target}</b>!",
        "effect_type": "none",
    },
    {
        "command": "slap",
        "name": "Дать пощёчину",
        "description": "Дать пощёчину другому игроку.",
        "cost": Decimal("7"),
        "success_text": "👋 <b>{actor}</b> дал пощёчину <b>{target}</b>!",
        "effect_type": "damage",
        "effect_value": 5,
    },
    {
        "command": "kick",
        "name": "Пнуть",
        "description": "Пнуть другого игрока.",
        "cost": Decimal("12"),
        "success_text": "🦵 <b>{actor}</b> пнул <b>{target}</b>!",
        "effect_type": "damage",
        "effect_value": 12,
    },
    {
        "command": "bite",
        "name": "Укусить",
        "description": "Укусить другого игрока.",
        "cost": Decimal("8"),
        "success_text": "🧛 <b>{actor}</b> укусил <b>{target}</b>!",
        "effect_type": "damage",
        "effect_value": 8,
    },
    {
        "command": "piss",
        "name": "Обоссать",
        "description": "Очень уважительное взаимодействие.",
        "cost": Decimal("15"),
        "success_text": "💦 <b>{actor}</b> обоссал <b>{target}</b>!",
        "effect_type": "none",
    },
)


# ============================================================================
# DEFAULT ADMIN LEVELS
# ============================================================================

DEFAULT_ADMIN_LEVELS = (
    {
        "name": "Модератор",
        "description": "Базовые права модерации.",
        "level": 10,
    },
    {
        "name": "Администратор",
        "description": "Расширенные права.",
        "level": 50,
    },
    {
        "name": "Старший администратор",
        "description": "Почти полный доступ.",
        "level": 80,
    },
)


async def _seed_races(session: AsyncSession) -> None:
    for data in DEFAULT_RACES:
        result = await session.execute(
            select(Race).where(
                Race.name == data["name"]
            )
        )

        if result.scalar_one_or_none() is None:
            session.add(Race(**data))


async def _seed_ranks(session: AsyncSession) -> None:
    for data in DEFAULT_RANKS:
        result = await session.execute(
            select(CharacterRank).where(
                CharacterRank.name == data["name"]
            )
        )

        if result.scalar_one_or_none() is None:
            session.add(CharacterRank(**data))


async def _seed_abilities(session: AsyncSession) -> None:
    for data in DEFAULT_ABILITIES:
        result = await session.execute(
            select(Ability).where(
                Ability.name == data["name"]
            )
        )

        if result.scalar_one_or_none() is None:
            session.add(Ability(**data))


async def _seed_items(session: AsyncSession) -> None:
    for data in DEFAULT_ITEMS:
        result = await session.execute(
            select(Item).where(
                Item.name == data["name"]
            )
        )

        if result.scalar_one_or_none() is None:
            session.add(Item(**data))


async def _seed_cases(session: AsyncSession) -> None:
    for data in DEFAULT_CASES:
        result = await session.execute(
            select(Case).where(
                Case.name == data["name"]
            )
        )

        case = result.scalar_one_or_none()

        if case is None:
            case = Case(
                name=data["name"],
                description=data["description"],
                price=data["price"],
                currency_type=data["currency_type"],
            )

            session.add(case)

            await session.flush()

            for reward_data in data["rewards"]:
                session.add(
                    CaseReward(
                        case_id=case.id,
                        **reward_data,
                    )
                )


async def _seed_interactions(
    session: AsyncSession,
) -> None:
    for data in DEFAULT_INTERACTIONS:
        result = await session.execute(
            select(InteractionType).where(
                InteractionType.command == data["command"]
            )
        )

        if result.scalar_one_or_none() is None:
            session.add(
                InteractionType(
                    command=data["command"],
                    name=data["name"],
                    description=data["description"],
                    cost=data["cost"],
                    currency_type="currency",
                    cooldown_seconds=5,
                    requires_target=True,
                    allow_self_target=False,
                    success_text=data["success_text"],
                    has_random_result=False,
                    success_chance=Decimal("100"),
                    effect_type=data["effect_type"],
                    effect_value=data.get(
                        "effect_value",
                        0,
                    ),
                )
            )


async def _seed_admin_levels(
    session: AsyncSession,
) -> None:
    for data in DEFAULT_ADMIN_LEVELS:
        result = await session.execute(
            select(AdminLevel).where(
                AdminLevel.level == data["level"]
            )
        )

        if result.scalar_one_or_none() is None:
            session.add(AdminLevel(**data))


async def seed_defaults(
    session: AsyncSession,
) -> None:
    """
    Идемпотентный первичный seed.

    Повторный запуск НЕ перезаписывает изменения Founder.
    Поэтому Founder может спокойно менять дефолтные записи.
    """

    await _seed_races(session)
    await _seed_ranks(session)
    await _seed_abilities(session)
    await _seed_items(session)
    await _seed_cases(session)
    await _seed_interactions(session)
    await _seed_admin_levels(session)

    await session.flush()