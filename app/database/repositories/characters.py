"""
Repository for RPG characters.

Repository отвечает только за работу с персонажами,
расами, рангами и способностями.

Бизнес-логика:
    - расчёт характеристик;
    - требования рангов;
    - применение эффектов;
    - cooldown способностей;
    - игровые правила

будет находиться в services/character.py.

Здесь только работа с БД.
"""

from datetime import datetime
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.character import (
    Ability,
    Character,
    CharacterAbility,
    CharacterRank,
    Race,
)


class CharacterRepository:
    """
    Репозиторий RPG-персонажей.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ========================================================================
    # CHARACTER
    # ========================================================================

    async def get_character(
        self,
        user_id: int,
    ) -> Character | None:
        """
        Получить персонажа пользователя.
        """

        result = await self.session.execute(
            select(Character).where(
                Character.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def create_character(
        self,
        *,
        user_id: int,
        name: str,
        race_id: int | None = None,
        rank_id: int | None = None,
    ) -> Character:
        """
        Создать персонажа.

        Начальные характеристики устанавливаются сервисом
        либо значениями модели.
        """

        character = Character(
            user_id=user_id,
            name=name,
            race_id=race_id,
            rank_id=rank_id,
        )

        self.session.add(character)

        await self.session.flush()

        return character

    async def get_or_create_character(
        self,
        *,
        user_id: int,
        name: str,
        race_id: int | None = None,
        rank_id: int | None = None,
    ) -> tuple[Character, bool]:
        """
        Получить персонажа или создать его.

        Возвращает:

            (character, created)
        """

        character = await self.get_character(user_id)

        if character is not None:
            return character, False

        character = await self.create_character(
            user_id=user_id,
            name=name,
            race_id=race_id,
            rank_id=rank_id,
        )

        return character, True

    async def update_character(
        self,
        user_id: int,
        **values: object,
    ) -> Character | None:
        """
        Обновить произвольные поля персонажа.

        Разрешённые поля проверяются вручную, чтобы случайно
        не изменить user_id или другие системные данные.
        """

        allowed_fields = {
            "name",
            "race_id",
            "rank_id",
            "level",
            "xp",
            "hp",
            "max_hp",
            "strength",
            "defense",
            "luck",
            "speed",
            "intelligence",
            "title",
            "bio",
            "is_active",
        }

        invalid_fields = set(values) - allowed_fields

        if invalid_fields:
            raise ValueError(
                f"Unsupported character fields: "
                f"{', '.join(sorted(invalid_fields))}"
            )

        character = await self.get_character(user_id)

        if character is None:
            return None

        for field, value in values.items():
            setattr(character, field, value)

        await self.session.flush()

        return character

    async def delete_character(
        self,
        user_id: int,
    ) -> bool:
        """
        Удалить персонажа пользователя.
        """

        result = await self.session.execute(
            delete(Character).where(
                Character.user_id == user_id,
            )
        )

        await self.session.flush()

        return result.rowcount > 0

    # ========================================================================
    # CHARACTER XP
    # ========================================================================

    async def add_xp(
        self,
        user_id: int,
        amount: int,
    ) -> Character | None:
        """
        Изменить XP персонажа.

        Расчёт уровня выполняется CharacterService.
        """

        character = await self.get_character(user_id)

        if character is None:
            return None

        character.xp += amount

        if character.xp < 0:
            character.xp = 0

        await self.session.flush()

        return character

    async def set_level(
        self,
        user_id: int,
        level: int,
    ) -> Character | None:
        """
        Установить уровень персонажа.
        """

        character = await self.get_character(user_id)

        if character is None:
            return None

        character.level = max(1, level)

        await self.session.flush()

        return character

    # ========================================================================
    # CHARACTER STATS
    # ========================================================================

    async def update_stats(
        self,
        user_id: int,
        *,
        hp: int | None = None,
        max_hp: int | None = None,
        strength: int | None = None,
        defense: int | None = None,
        luck: int | None = None,
        speed: int | None = None,
        intelligence: int | None = None,
    ) -> Character | None:
        """
        Обновить характеристики персонажа.
        """

        character = await self.get_character(user_id)

        if character is None:
            return None

        if hp is not None:
            character.hp = max(0, hp)

        if max_hp is not None:
            character.max_hp = max(1, max_hp)

        if strength is not None:
            character.strength = max(0, strength)

        if defense is not None:
            character.defense = max(0, defense)

        if luck is not None:
            character.luck = max(0, luck)

        if speed is not None:
            character.speed = max(0, speed)

        if intelligence is not None:
            character.intelligence = max(0, intelligence)

        # HP не должен превышать max_hp.

        if character.hp > character.max_hp:
            character.hp = character.max_hp

        await self.session.flush()

        return character

    async def heal(
        self,
        user_id: int,
        amount: int,
    ) -> Character | None:
        """
        Восстановить HP.
        """

        if amount <= 0:
            return await self.get_character(user_id)

        character = await self.get_character(user_id)

        if character is None:
            return None

        character.hp = min(
            character.max_hp,
            character.hp + amount,
        )

        await self.session.flush()

        return character

    async def damage(
        self,
        user_id: int,
        amount: int,
    ) -> Character | None:
        """
        Нанести персонажу урон.

        Если HP становится меньше нуля — устанавливается 0.
        """

        if amount <= 0:
            return await self.get_character(user_id)

        character = await self.get_character(user_id)

        if character is None:
            return None

        character.hp = max(
            0,
            character.hp - amount,
        )

        await self.session.flush()

        return character

    # ========================================================================
    # RACES
    # ========================================================================

    async def get_race(
        self,
        race_id: int,
    ) -> Race | None:
        """
        Получить расу по ID.
        """

        result = await self.session.execute(
            select(Race).where(
                Race.id == race_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_race_by_name(
        self,
        name: str,
    ) -> Race | None:
        """
        Получить расу по названию.
        """

        result = await self.session.execute(
            select(Race).where(
                Race.name.ilike(name.strip()),
            )
        )

        return result.scalar_one_or_none()

    async def get_active_races(
        self,
    ) -> Sequence[Race]:
        """
        Получить все активные расы.
        """

        result = await self.session.execute(
            select(Race)
            .where(Race.is_active.is_(True))
            .order_by(Race.id)
        )

        return result.scalars().all()

    async def create_race(
        self,
        *,
        name: str,
        description: str = "",
        base_hp: int = 100,
        base_strength: int = 10,
        base_defense: int = 10,
        base_luck: int = 10,
        base_speed: int = 10,
        base_intelligence: int = 10,
    ) -> Race:
        """
        Создать расу.

        Founder Panel будет использовать этот метод.
        """

        race = Race(
            name=name.strip(),
            description=description,
            base_hp=max(1, base_hp),
            base_strength=max(0, base_strength),
            base_defense=max(0, base_defense),
            base_luck=max(0, base_luck),
            base_speed=max(0, base_speed),
            base_intelligence=max(0, base_intelligence),
        )

        self.session.add(race)

        await self.session.flush()

        return race

    async def update_race(
        self,
        race_id: int,
        **values: object,
    ) -> Race | None:
        """
        Изменить параметры расы.
        """

        allowed_fields = {
            "name",
            "description",
            "base_hp",
            "base_strength",
            "base_defense",
            "base_luck",
            "base_speed",
            "base_intelligence",
            "is_active",
        }

        invalid_fields = set(values) - allowed_fields

        if invalid_fields:
            raise ValueError(
                f"Unsupported race fields: "
                f"{', '.join(sorted(invalid_fields))}"
            )

        race = await self.get_race(race_id)

        if race is None:
            return None

        for field, value in values.items():
            setattr(race, field, value)

        await self.session.flush()

        return race

    # ========================================================================
    # RANKS
    # ========================================================================

    async def get_rank(
        self,
        rank_id: int,
    ) -> CharacterRank | None:
        """
        Получить ранг.
        """

        result = await self.session.execute(
            select(CharacterRank).where(
                CharacterRank.id == rank_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_rank_by_level(
        self,
        level: int,
    ) -> CharacterRank | None:
        """
        Получить ранг по его порядковому уровню.
        """

        result = await self.session.execute(
            select(CharacterRank).where(
                CharacterRank.level == level,
            )
        )

        return result.scalar_one_or_none()

    async def get_active_ranks(
        self,
    ) -> Sequence[CharacterRank]:
        """
        Получить активные ранги по порядку.
        """

        result = await self.session.execute(
            select(CharacterRank)
            .where(CharacterRank.is_active.is_(True))
            .order_by(CharacterRank.level)
        )

        return result.scalars().all()

    async def create_rank(
        self,
        *,
        name: str,
        level: int,
        description: str = "",
        required_level: int = 1,
        required_xp: int = 0,
        required_reputation: int = 0,
        hp_bonus: int = 0,
        strength_bonus: int = 0,
        defense_bonus: int = 0,
        luck_bonus: int = 0,
        speed_bonus: int = 0,
        intelligence_bonus: int = 0,
    ) -> CharacterRank:
        """
        Создать ранг персонажа.
        """

        rank = CharacterRank(
            name=name.strip(),
            level=max(1, level),
            description=description,
            required_level=max(1, required_level),
            required_xp=max(0, required_xp),
            required_reputation=max(0, required_reputation),
            hp_bonus=hp_bonus,
            strength_bonus=strength_bonus,
            defense_bonus=defense_bonus,
            luck_bonus=luck_bonus,
            speed_bonus=speed_bonus,
            intelligence_bonus=intelligence_bonus,
        )

        self.session.add(rank)

        await self.session.flush()

        return rank

    async def update_rank(
        self,
        rank_id: int,
        **values: object,
    ) -> CharacterRank | None:
        """
        Изменить параметры ранга.
        """

        allowed_fields = {
            "name",
            "description",
            "level",
            "required_level",
            "required_xp",
            "required_reputation",
            "hp_bonus",
            "strength_bonus",
            "defense_bonus",
            "luck_bonus",
            "speed_bonus",
            "intelligence_bonus",
            "is_active",
        }

        invalid_fields = set(values) - allowed_fields

        if invalid_fields:
            raise ValueError(
                f"Unsupported rank fields: "
                f"{', '.join(sorted(invalid_fields))}"
            )

        rank = await self.get_rank(rank_id)

        if rank is None:
            return None

        for field, value in values.items():
            setattr(rank, field, value)

        await self.session.flush()

        return rank

    # ========================================================================
    # ABILITIES
    # ========================================================================

    async def get_ability(
        self,
        ability_id: int,
    ) -> Ability | None:
        """
        Получить способность.
        """

        result = await self.session.execute(
            select(Ability).where(
                Ability.id == ability_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_ability_by_name(
        self,
        name: str,
    ) -> Ability | None:
        """
        Получить способность по названию.
        """

        result = await self.session.execute(
            select(Ability).where(
                Ability.name.ilike(name.strip()),
            )
        )

        return result.scalar_one_or_none()

    async def get_active_abilities(
        self,
    ) -> Sequence[Ability]:
        """
        Получить активные способности.
        """

        result = await self.session.execute(
            select(Ability)
            .where(Ability.is_active.is_(True))
            .order_by(Ability.id)
        )

        return result.scalars().all()

    async def create_ability(
        self,
        *,
        name: str,
        description: str = "",
        ability_type: str,
        effect_value: int = 0,
        duration_seconds: int = 0,
        cooldown_seconds: int = 0,
    ) -> Ability:
        """
        Создать способность.
        """

        ability = Ability(
            name=name.strip(),
            description=description,
            ability_type=ability_type,
            effect_value=effect_value,
            duration_seconds=max(0, duration_seconds),
            cooldown_seconds=max(0, cooldown_seconds),
        )

        self.session.add(ability)

        await self.session.flush()

        return ability

    async def update_ability(
        self,
        ability_id: int,
        **values: object,
    ) -> Ability | None:
        """
        Изменить способность.
        """

        allowed_fields = {
            "name",
            "description",
            "ability_type",
            "effect_value",
            "duration_seconds",
            "cooldown_seconds",
            "is_active",
        }

        invalid_fields = set(values) - allowed_fields

        if invalid_fields:
            raise ValueError(
                f"Unsupported ability fields: "
                f"{', '.join(sorted(invalid_fields))}"
            )

        ability = await self.get_ability(ability_id)

        if ability is None:
            return None

        for field, value in values.items():
            setattr(ability, field, value)

        await self.session.flush()

        return ability

    # ========================================================================
    # CHARACTER ABILITIES
    # ========================================================================

    async def get_character_abilities(
        self,
        user_id: int,
    ) -> Sequence[CharacterAbility]:
        """
        Получить способности персонажа.
        """

        result = await self.session.execute(
            select(CharacterAbility)
            .where(
                CharacterAbility.user_id == user_id,
                CharacterAbility.is_active.is_(True),
            )
            .order_by(CharacterAbility.id)
        )

        return result.scalars().all()

    async def get_character_ability(
        self,
        user_id: int,
        ability_id: int,
    ) -> CharacterAbility | None:
        """
        Получить конкретную способность персонажа.
        """

        result = await self.session.execute(
            select(CharacterAbility).where(
                CharacterAbility.user_id == user_id,
                CharacterAbility.ability_id == ability_id,
            )
        )

        return result.scalar_one_or_none()

    async def add_ability_to_character(
        self,
        *,
        user_id: int,
        ability_id: int,
    ) -> CharacterAbility:
        """
        Выдать способность персонажу.

        Если связь уже существует — активируем её повторно,
        вместо создания дубликата.
        """

        existing = await self.get_character_ability(
            user_id=user_id,
            ability_id=ability_id,
        )

        if existing is not None:
            existing.is_active = True

            await self.session.flush()

            return existing

        character_ability = CharacterAbility(
            user_id=user_id,
            ability_id=ability_id,
        )

        self.session.add(character_ability)

        await self.session.flush()

        return character_ability

    async def remove_ability_from_character(
        self,
        *,
        user_id: int,
        ability_id: int,
    ) -> bool:
        """
        Удалить способность у персонажа.
        """

        character_ability = await self.get_character_ability(
            user_id=user_id,
            ability_id=ability_id,
        )

        if character_ability is None:
            return False

        await self.session.delete(character_ability)

        await self.session.flush()

        return True

    async def set_ability_cooldown(
        self,
        *,
        user_id: int,
        ability_id: int,
        cooldown_until: datetime | None,
    ) -> CharacterAbility | None:
        """
        Установить время окончания cooldown способности.
        """

        character_ability = await self.get_character_ability(
            user_id=user_id,
            ability_id=ability_id,
        )

        if character_ability is None:
            return None

        character_ability.cooldown_until = cooldown_until

        await self.session.flush()

        return character_ability

    async def set_ability_effect(
        self,
        *,
        user_id: int,
        ability_id: int,
        effect_until: datetime | None,
    ) -> CharacterAbility | None:
        """
        Установить время окончания временного эффекта.
        """

        character_ability = await self.get_character_ability(
            user_id=user_id,
            ability_id=ability_id,
        )

        if character_ability is None:
            return None

        character_ability.effect_until = effect_until

        await self.session.flush()

        return character_ability