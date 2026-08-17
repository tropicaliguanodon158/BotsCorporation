from __future__ import annotations

from dataclasses import dataclass

from app.database.repositories.characters import CharacterRepository
from app.database.repositories.economy import EconomyRepository
from app.database.repositories.users import UserRepository
from app.services.character import CharacterService


@dataclass(slots=True)
class ProgressionResult:
    user_id: int

    xp: int = 0

    level_before: int = 1
    level_after: int = 1

    levels_gained: int = 0

    rank_before_id: int | None = None
    rank_after_id: int | None = None

    rank_before_name: str | None = None
    rank_after_name: str | None = None

    rank_up: bool = False

    level_reward_currency: int = 0
    level_reward_gems: int = 0

    character_exists: bool = False


class ProgressionService:
    """
    Единая система прогрессии персонажа.

    Отвечает за:

        XP персонажа
        ↓
        повышение уровня
        ↓
        награды за уровни
        ↓
        автоматическое повышение ранга

    Telegram API здесь НЕ используется.
    """

    DEFAULT_LEVEL_REWARD_CURRENCY = 10
    DEFAULT_LEVEL_REWARD_GEMS = 1

    MAX_LEVEL = 1000

    def __init__(self, session) -> None:
        self.session = session

        self.characters = CharacterRepository(session)
        self.economy = EconomyRepository(session)
        self.users = UserRepository(session)

        self.character_service = CharacterService(
            self.characters
        )

    async def add_xp(
        self,
        *,
        user_id: int,
        amount: int,
    ) -> ProgressionResult:
        if amount <= 0:
            raise ValueError(
                "XP amount must be greater than zero."
            )

        before = await self.characters.get_character(
            user_id
        )

        if before is None:
            return ProgressionResult(
                user_id=user_id,
                xp=amount,
                character_exists=False,
            )

        level_before = before.level
        rank_before_id = before.rank_id

        rank_before = None

        if rank_before_id is not None:
            rank_before = await self.characters.get_rank(
                rank_before_id
            )

        character = await self.character_service.add_xp(
            user_id=user_id,
            amount=amount,
        )

        level_after = character.level
        rank_after_id = character.rank_id

        rank_after = None

        if rank_after_id is not None:
            rank_after = await self.characters.get_rank(
                rank_after_id
            )

        levels_gained = max(
            0,
            level_after - level_before,
        )

        reward_currency = (
            levels_gained
            * self.DEFAULT_LEVEL_REWARD_CURRENCY
        )

        reward_gems = (
            levels_gained
            * self.DEFAULT_LEVEL_REWARD_GEMS
        )

        if reward_currency > 0:
            await self.economy.add_balance(
                user_id=user_id,
                amount=reward_currency,
                transaction_type="level_reward",
                source="level_up",
            )

        if reward_gems > 0:
            await self.economy.add_gems(
                user_id=user_id,
                amount=reward_gems,
            )

        await self.session.flush()

        return ProgressionResult(
            user_id=user_id,
            xp=amount,
            level_before=level_before,
            level_after=level_after,
            levels_gained=levels_gained,
            rank_before_id=rank_before_id,
            rank_after_id=rank_after_id,
            rank_before_name=(
                rank_before.name
                if rank_before is not None
                else None
            ),
            rank_after_name=(
                rank_after.name
                if rank_after is not None
                else None
            ),
            rank_up=(
                rank_before_id != rank_after_id
                and rank_after_id is not None
            ),
            level_reward_currency=reward_currency,
            level_reward_gems=reward_gems,
            character_exists=True,
        )