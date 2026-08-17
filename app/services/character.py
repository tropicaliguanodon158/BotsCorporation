from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence

from app.database.models.character import (
    Ability,
    Character,
    CharacterRank,
    Race,
)
from app.database.repositories.characters import CharacterRepository


class CharacterService:
    """
    Бизнес-логика RPG-персонажей.

    Repository отвечает только за БД.
    Здесь находятся:
        - создание персонажа;
        - XP и уровни;
        - применение расы;
        - повышение ранга;
        - лечение/урон;
        - проверка способностей.
    """

    def __init__(
        self,
        repository: CharacterRepository,
    ) -> None:
        self.repository = repository

    # ========================================================================
    # CHARACTER
    # ========================================================================

    async def get_character(
        self,
        user_id: int,
    ) -> Character | None:
        return await self.repository.get_character(user_id)

    async def create_character(
        self,
        *,
        user_id: int,
        name: str,
        race_id: int | None = None,
        rank_id: int | None = None,
    ) -> Character:
        name = name.strip()

        if not name:
            raise ValueError(
                "Character name cannot be empty."
            )

        if len(name) > 100:
            raise ValueError(
                "Character name cannot exceed 100 characters."
            )

        existing = await self.repository.get_character(user_id)

        if existing is not None:
            raise ValueError(
                "User already has a character."
            )

        race = None

        if race_id is not None:
            race = await self.repository.get_race(race_id)

            if race is None or not race.is_active:
                raise ValueError(
                    "Selected race does not exist or is inactive."
                )

        rank = None

        if rank_id is not None:
            rank = await self.repository.get_rank(rank_id)

            if rank is None or not rank.is_active:
                raise ValueError(
                    "Selected rank does not exist or is inactive."
                )

        if race is None:
            character = await self.repository.create_character(
                user_id=user_id,
                name=name,
                race_id=None,
                rank_id=rank_id,
            )
        else:
            character = await self.repository.create_character(
                user_id=user_id,
                name=name,
                race_id=race.id,
                rank_id=rank_id,
            )

            await self.repository.update_stats(
                user_id,
                hp=race.base_hp,
                max_hp=race.base_hp,
                strength=race.base_strength,
                defense=race.base_defense,
                luck=race.base_luck,
                speed=race.base_speed,
                intelligence=race.base_intelligence,
            )

            character = await self.repository.get_character(user_id)

            if character is None:
                raise RuntimeError(
                    "Character disappeared after creation."
                )

        if rank is not None:
            await self._apply_rank_stats(
                character,
                rank,
            )

        return character

    async def get_or_create_character(
        self,
        *,
        user_id: int,
        name: str,
        race_id: int | None = None,
        rank_id: int | None = None,
    ) -> tuple[Character, bool]:
        existing = await self.repository.get_character(user_id)

        if existing is not None:
            return existing, False

        character = await self.create_character(
            user_id=user_id,
            name=name,
            race_id=race_id,
            rank_id=rank_id,
        )

        return character, True

    async def rename(
        self,
        *,
        user_id: int,
        name: str,
    ) -> Character:
        name = name.strip()

        if not name:
            raise ValueError(
                "Character name cannot be empty."
            )

        if len(name) > 100:
            raise ValueError(
                "Character name cannot exceed 100 characters."
            )

        character = await self.repository.update_character(
            user_id,
            name=name,
        )

        if character is None:
            raise ValueError(
                "Character does not exist."
            )

        return character

    async def update_profile(
        self,
        *,
        user_id: int,
        title: str | None = None,
        bio: str | None = None,
    ) -> Character:
        if title is not None:
            title = title.strip()

            if len(title) > 100:
                raise ValueError(
                    "Title cannot exceed 100 characters."
                )

        if bio is not None:
            bio = bio.strip()

            if len(bio) > 5000:
                raise ValueError(
                    "Bio cannot exceed 5000 characters."
                )

        character = await self.repository.update_character(
            user_id,
            title=title,
            bio=bio,
        )

        if character is None:
            raise ValueError(
                "Character does not exist."
            )

        return character

    # ========================================================================
    # XP / LEVEL
    # ========================================================================

    @staticmethod
    def xp_for_level(level: int) -> int:
        """
        XP для достижения указанного уровня.

        Уровень 1:
            0 XP

        Уровень 2:
            400 XP

        Уровень 3:
            900 XP

        Уровень 4:
            1600 XP

        Формула:

            100 * level²
        """

        level = max(1, level)

        return 100 * level * level

    async def add_xp(
        self,
        *,
        user_id: int,
        amount: int,
    ) -> Character:
        if amount <= 0:
            raise ValueError(
                "XP amount must be greater than zero."
            )

        character = await self.repository.add_xp(
            user_id,
            amount,
        )

        if character is None:
            raise ValueError(
                "Character does not exist."
            )

        await self._recalculate_level(
            character
        )

        return character

    async def _recalculate_level(
        self,
        character: Character,
    ) -> Character:
        """
        Пересчитывает уровень и автоматически назначает
        максимально доступный ранг.

        Один большой XP reward может поднять персонажа
        сразу на несколько уровней.
        """

        old_level = character.level

        new_level = 1

        while (
            new_level < 1000
            and character.xp >= self.xp_for_level(
                new_level + 1
            )
        ):
            new_level += 1

        # ========================================================================
        # LEVEL
        # ========================================================================

        if new_level != old_level:
            await self.repository.set_level(
                character.user_id,
                new_level,
            )

            level_difference = (
                new_level - old_level
            )

            if level_difference > 0:
                await self.repository.update_stats(
                    character.user_id,
                    max_hp=(
                        character.max_hp
                        + level_difference * 5
                    ),
                    hp=(
                        character.hp
                        + level_difference * 5
                    ),
                    strength=(
                        character.strength
                        + level_difference
                    ),
                )

        # ========================================================================
        # AUTOMATIC RANK
        # ========================================================================

        character = await self.repository.get_character(
            character.user_id
        )

        if character is None:
            raise RuntimeError(
                "Character disappeared during level recalculation."
            )

        ranks = await self.repository.get_active_ranks()

        eligible_rank = None

        for rank in ranks:
            # У персонажа пока нет отдельного reputation-поля.
            # Поэтому rank с reputation requirement > 0
            # автоматически не назначается.
            if rank.required_reputation > 0:
                continue

            if character.level < rank.required_level:
                continue

            if character.xp < rank.required_xp:
                continue

            # Берём только ранг выше текущего.
            if (
                character.rank_id is not None
                and rank.id == character.rank_id
            ):
                eligible_rank = rank
                continue

            if (
                character.rank_id is not None
            ):
                current_rank = await self.repository.get_rank(
                    character.rank_id
                )

                if (
                    current_rank is not None
                    and rank.level <= current_rank.level
                ):
                    continue

            eligible_rank = rank

        # ========================================================================
        # APPLY RANK
        # ========================================================================

        if (
            eligible_rank is not None
            and eligible_rank.id != character.rank_id
        ):
            old_rank = None

            if character.rank_id is not None:
                old_rank = await self.repository.get_rank(
                    character.rank_id
                )

            await self.repository.update_character(
                character.user_id,
                rank_id=eligible_rank.id,
            )

            # При первом назначении применяем весь бонус.
            #
            # При переходе с одного ранга на другой
            # применяем разницу между бонусами.
            #
            # Благодаря этому:
            #
            # Новобранец +5 STR
            # Воин +10 STR
            #
            # переход даст +5 STR, а не +10.
            old_hp = (
                old_rank.hp_bonus
                if old_rank is not None
                else 0
            )

            old_strength = (
                old_rank.strength_bonus
                if old_rank is not None
                else 0
            )

            old_defense = (
                old_rank.defense_bonus
                if old_rank is not None
                else 0
            )

            old_luck = (
                old_rank.luck_bonus
                if old_rank is not None
                else 0
            )

            old_speed = (
                old_rank.speed_bonus
                if old_rank is not None
                else 0
            )

            old_intelligence = (
                old_rank.intelligence_bonus
                if old_rank is not None
                else 0
            )

            await self.repository.update_stats(
                character.user_id,
                max_hp=(
                    character.max_hp
                    + eligible_rank.hp_bonus
                    - old_hp
                ),
                hp=(
                    character.hp
                    + eligible_rank.hp_bonus
                    - old_hp
                ),
                strength=(
                    character.strength
                    + eligible_rank.strength_bonus
                    - old_strength
                ),
                defense=(
                    character.defense
                    + eligible_rank.defense_bonus
                    - old_defense
                ),
                luck=(
                    character.luck
                    + eligible_rank.luck_bonus
                    - old_luck
                ),
                speed=(
                    character.speed
                    + eligible_rank.speed_bonus
                    - old_speed
                ),
                intelligence=(
                    character.intelligence
                    + eligible_rank.intelligence_bonus
                    - old_intelligence
                ),
            )

        refreshed = await self.repository.get_character(
            character.user_id
        )

        if refreshed is None:
            raise RuntimeError(
                "Character disappeared during level recalculation."
            )

        return refreshed

    # ========================================================================
    # RACE
    # ========================================================================

    async def change_race(
        self,
        *,
        user_id: int,
        race_id: int,
    ) -> Character:
        race = await self.repository.get_race(race_id)

        if race is None or not race.is_active:
            raise ValueError(
                "Race does not exist or is inactive."
            )

        character = await self.repository.get_character(user_id)

        if character is None:
            raise ValueError(
                "Character does not exist."
            )

        await self.repository.update_character(
            user_id,
            race_id=race.id,
        )

        await self.repository.update_stats(
            user_id,
            max_hp=race.base_hp,
            hp=race.base_hp,
            strength=race.base_strength,
            defense=race.base_defense,
            luck=race.base_luck,
            speed=race.base_speed,
            intelligence=race.base_intelligence,
        )

        refreshed = await self.repository.get_character(user_id)

        if refreshed is None:
            raise RuntimeError(
                "Character disappeared after race change."
            )

        return refreshed

    async def get_active_races(
        self,
    ) -> Sequence[Race]:
        return await self.repository.get_active_races()

    # ========================================================================
    # RANK
    # ========================================================================

    async def check_rank_requirements(
        self,
        *,
        character: Character,
        rank: CharacterRank,
    ) -> bool:
        return (
            character.level >= rank.required_level
            and character.xp >= rank.required_xp
        )

    async def promote(
        self,
        *,
        user_id: int,
        rank_id: int,
    ) -> Character:
        character = await self.repository.get_character(user_id)

        if character is None:
            raise ValueError(
                "Character does not exist."
            )

        rank = await self.repository.get_rank(rank_id)

        if rank is None or not rank.is_active:
            raise ValueError(
                "Rank does not exist or is inactive."
            )

        if not await self.check_rank_requirements(
            character=character,
            rank=rank,
        ):
            raise ValueError(
                "Character does not meet rank requirements."
            )

        if (
            character.rank_id is not None
            and character.rank_id == rank.id
        ):
            return character

        await self.repository.update_character(
            user_id,
            rank_id=rank.id,
        )

        await self._apply_rank_stats(
            character,
            rank,
        )

        refreshed = await self.repository.get_character(user_id)

        if refreshed is None:
            raise RuntimeError(
                "Character disappeared after promotion."
            )

        return refreshed

    async def _apply_rank_stats(
        self,
        character: Character,
        rank: CharacterRank,
    ) -> None:
        await self.repository.update_stats(
            character.user_id,
            max_hp=character.max_hp + rank.hp_bonus,
            hp=character.hp + rank.hp_bonus,
            strength=character.strength + rank.strength_bonus,
            defense=character.defense + rank.defense_bonus,
            luck=character.luck + rank.luck_bonus,
            speed=character.speed + rank.speed_bonus,
            intelligence=(
                character.intelligence
                + rank.intelligence_bonus
            ),
        )

    async def get_active_ranks(
        self,
    ) -> Sequence[CharacterRank]:
        return await self.repository.get_active_ranks()

    # ========================================================================
    # HP
    # ========================================================================

    async def heal(
        self,
        *,
        user_id: int,
        amount: int,
    ) -> Character:
        if amount <= 0:
            raise ValueError(
                "Heal amount must be greater than zero."
            )

        character = await self.repository.heal(
            user_id,
            amount,
        )

        if character is None:
            raise ValueError(
                "Character does not exist."
            )

        return character

    async def damage(
        self,
        *,
        user_id: int,
        amount: int,
    ) -> Character:
        if amount <= 0:
            raise ValueError(
                "Damage amount must be greater than zero."
            )

        character = await self.repository.damage(
            user_id,
            amount,
        )

        if character is None:
            raise ValueError(
                "Character does not exist."
            )

        return character

    async def restore_full_hp(
        self,
        *,
        user_id: int,
    ) -> Character:
        character = await self.repository.get_character(user_id)

        if character is None:
            raise ValueError(
                "Character does not exist."
            )

        return await self.repository.update_stats(
            user_id,
            hp=character.max_hp,
        )  # type: ignore[return-value]

    # ========================================================================
    # SERIALIZATION
    # ========================================================================

    @staticmethod
    def to_dict(
        character: Character,
    ) -> dict[str, Any]:
        return {
            "user_id": character.user_id,
            "name": character.name,
            "race_id": character.race_id,
            "rank_id": character.rank_id,
            "level": character.level,
            "xp": character.xp,
            "hp": character.hp,
            "max_hp": character.max_hp,
            "strength": character.strength,
            "defense": character.defense,
            "luck": character.luck,
            "speed": character.speed,
            "intelligence": character.intelligence,
            "title": character.title,
            "bio": character.bio,
            "is_active": character.is_active,
            "created_at": character.created_at,
            "updated_at": character.updated_at,
        }