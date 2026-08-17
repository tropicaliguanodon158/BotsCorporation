"""
Games service.

Бизнес-логика игровых механик.

Repository:
    GamesRepository -> игровые сессии, игроки, ставки.

EconomyRepository:
    - списание ставок;
    - начисление выплат.

Service:
    - проверяет баланс;
    - создаёт игру;
    - фиксирует ставку;
    - выполняет игру;
    - начисляет выплату;
    - завершает игру.

commit()/rollback() здесь НЕ выполняются.
"""

from __future__ import annotations

import random
from decimal import Decimal
from typing import Any, Sequence

from app.database.models.games import Game, GamePlayer
from app.database.repositories.economy import EconomyRepository
from app.database.repositories.games import GamesRepository


class GamesService:
    """
    Игровая бизнес-логика.
    """

    ACTIVE_STATUSES = {
        "created",
        "waiting",
        "active",
    }

    GAME_TYPES = {
        "roulette",
        "blackjack",
        "dice",
        "duel",
        "coinflip",
    }

    def __init__(
        self,
        repository: GamesRepository,
        economy_repository: EconomyRepository,
    ) -> None:
        self.repository = repository
        self.economy = economy_repository

    # ========================================================================
    # COMMON
    # ========================================================================

    async def get_game(
        self,
        game_id: int,
    ) -> Game | None:
        return await self.repository.get_game(game_id)

    async def create(
        self,
        *,
        game_type: str,
        creator_id: int,
        chat_id: int | None = None,
        pot: Decimal | int | float | str = Decimal("0.00"),
        game_data: dict[str, Any] | None = None,
    ) -> Game:
        game_type = game_type.strip().lower()

        if game_type not in self.GAME_TYPES:
            raise ValueError(
                f"Unsupported game type: {game_type}"
            )

        existing = await self.repository.get_active_game(
            game_type=game_type,
            creator_id=creator_id,
            chat_id=chat_id,
        )

        if existing is not None:
            raise ValueError(
                "User already has an active game of this type."
            )

        return await self.repository.create_game(
            game_type=game_type,
            creator_id=creator_id,
            chat_id=chat_id,
            pot=pot,
            game_data=game_data,
        )

    async def cancel(
        self,
        game_id: int,
    ) -> Game:
        game = await self.repository.cancel_game(game_id)

        if game is None:
            raise ValueError(
                "Game does not exist."
            )

        return game

    # ========================================================================
    # PLAYERS
    # ========================================================================

    async def join(
        self,
        *,
        game_id: int,
        user_id: int,
        bet: Decimal | int | float | str = Decimal("0.00"),
    ) -> GamePlayer:
        game = await self.repository.get_game(game_id)

        if game is None:
            raise ValueError(
                "Game does not exist."
            )

        if game.status not in {
            "created",
            "waiting",
        }:
            raise ValueError(
                "Game is no longer accepting players."
            )

        if game.creator_id == user_id:
            existing = await self.repository.get_player(
                game_id=game_id,
                user_id=user_id,
            )

            if existing is not None:
                return existing

        return await self.repository.add_player(
            game_id=game_id,
            user_id=user_id,
            bet=bet,
        )

    async def players(
        self,
        game_id: int,
    ) -> Sequence[GamePlayer]:
        return await self.repository.get_game_players(game_id)

    # ========================================================================
    # FINANCE
    # ========================================================================

    async def _charge(
        self,
        *,
        user_id: int,
        amount: Decimal,
        source: str,
        reference_id: str,
    ) -> None:
        amount = Decimal(str(amount))

        if amount <= 0:
            raise ValueError(
                "Bet amount must be greater than zero."
            )

        transaction = await self.economy.remove_balance(
            user_id=user_id,
            amount=amount,
            transaction_type="game_bet",
            source=source,
            reference_id=reference_id,
        )

        if transaction is None:
            raise ValueError(
                "Insufficient balance."
            )

    async def _payout(
        self,
        *,
        user_id: int,
        amount: Decimal,
        source: str,
        reference_id: str,
    ) -> None:
        amount = Decimal(str(amount))

        if amount <= 0:
            return

        await self.economy.add_balance(
            user_id=user_id,
            amount=amount,
            transaction_type="game_payout",
            source=source,
            reference_id=reference_id,
        )

    async def place_bet(
        self,
        *,
        game_id: int,
        user_id: int,
        amount: Decimal | int | float | str,
        bet_type: str,
        selection: str | None = None,
    ):
        game = await self.repository.get_game(game_id)

        if game is None:
            raise ValueError(
                "Game does not exist."
            )

        if game.status not in self.ACTIVE_STATUSES:
            raise ValueError(
                "Game is not active."
            )

        amount = Decimal(str(amount))

        if amount <= 0:
            raise ValueError(
                "Bet amount must be greater than zero."
            )

        await self._charge(
            user_id=user_id,
            amount=amount,
            source=f"game:{game.game_type}",
            reference_id=game.round_id,
        )

        try:
            bet = await self.repository.create_bet(
                game_id=game_id,
                user_id=user_id,
                amount=amount,
                bet_type=bet_type,
                selection=selection,
            )
        except Exception:
            await self._payout(
                user_id=user_id,
                amount=amount,
                source="game_bet_rollback",
                reference_id=game.round_id,
            )
            raise

        game.pot += amount
        await self.repository.update_game(
            game.id,
            pot=game.pot,
        )

        return bet

    # ========================================================================
    # DICE
    # ========================================================================

    async def dice(
        self,
        *,
        user_id: int,
        chat_id: int | None,
        bet: Decimal | int | float | str,
        sides: int = 6,
        target: int | None = None,
    ) -> dict[str, Any]:
        if sides < 2 or sides > 100:
            raise ValueError(
                "Dice sides must be between 2 and 100."
            )

        if target is not None and not 1 <= target <= sides:
            raise ValueError(
                "Dice target is outside the dice range."
            )

        amount = Decimal(str(bet))

        if amount <= 0:
            raise ValueError(
                "Bet amount must be greater than zero."
            )

        if await self.economy.get_balance(user_id) < amount:
            raise ValueError(
                "Insufficient balance."
            )

        game = await self.create(
            game_type="dice",
            creator_id=user_id,
            chat_id=chat_id,
        )

        await self.join(
            game_id=game.id,
            user_id=user_id,
            bet=amount,
        )

        await self.place_bet(
            game_id=game.id,
            user_id=user_id,
            amount=amount,
            bet_type="dice",
            selection=(
                str(target)
                if target is not None
                else "high"
            ),
        )

        await self.repository.start_game(game.id)

        roll = random.randint(1, sides)

        won = (
            roll == target
            if target is not None
            else roll > sides // 2
        )

        payout = (
            amount * Decimal(str(sides))
            if target is not None and won
            else amount * Decimal("1.90")
            if target is None and won
            else Decimal("0.00")
        )

        await self.repository.set_player_result(
            game_id=game.id,
            user_id=user_id,
            result="winner" if won else "loser",
            payout=payout,
        )

        if won:
            await self._payout(
                user_id=user_id,
                amount=payout,
                source="game:dice",
                reference_id=game.round_id,
            )

        await self.repository.finish_game(
            game.id,
            winner_id=user_id if won else None,
        )

        return {
            "game_id": game.id,
            "game_type": "dice",
            "roll": roll,
            "sides": sides,
            "target": target,
            "bet": amount,
            "won": won,
            "payout": payout,
        }

    # ========================================================================
    # COINFLIP
    # ========================================================================

    async def coinflip(
        self,
        *,
        user_id: int,
        chat_id: int | None,
        bet: Decimal | int | float | str,
        selection: str,
    ) -> dict[str, Any]:
        aliases = {
            "орёл": "heads",
            "орел": "heads",
            "heads": "heads",
            "h": "heads",
            "решка": "tails",
            "tails": "tails",
            "t": "tails",
        }

        selection = aliases.get(
            selection.strip().lower(),
            selection.strip().lower(),
        )

        if selection not in {
            "heads",
            "tails",
        }:
            raise ValueError(
                "Coin selection must be heads or tails."
            )

        amount = Decimal(str(bet))

        if amount <= 0:
            raise ValueError(
                "Bet amount must be greater than zero."
            )

        if await self.economy.get_balance(user_id) < amount:
            raise ValueError(
                "Insufficient balance."
            )

        game = await self.create(
            game_type="coinflip",
            creator_id=user_id,
            chat_id=chat_id,
        )

        await self.join(
            game_id=game.id,
            user_id=user_id,
            bet=amount,
        )

        await self.place_bet(
            game_id=game.id,
            user_id=user_id,
            amount=amount,
            bet_type="coinflip",
            selection=selection,
        )

        await self.repository.start_game(game.id)

        result = random.choice([
            "heads",
            "tails",
        ])

        won = result == selection

        payout = (
            amount * Decimal("1.90")
            if won
            else Decimal("0.00")
        )

        await self.repository.set_player_result(
            game_id=game.id,
            user_id=user_id,
            result="winner" if won else "loser",
            payout=payout,
        )

        if won:
            await self._payout(
                user_id=user_id,
                amount=payout,
                source="game:coinflip",
                reference_id=game.round_id,
            )

        await self.repository.finish_game(
            game.id,
            winner_id=user_id if won else None,
        )

        return {
            "game_id": game.id,
            "game_type": "coinflip",
            "selection": selection,
            "result": result,
            "bet": amount,
            "won": won,
            "payout": payout,
        }

    # ========================================================================
    # ROULETTE
    # ========================================================================

    async def roulette(
        self,
        *,
        user_id: int,
        chat_id: int | None,
        bet: Decimal | int | float | str,
        selection: str,
    ) -> dict[str, Any]:
        selection = selection.strip().lower()

        aliases = {
            "красное": "red",
            "красный": "red",
            "черное": "black",
            "чёрное": "black",
            "черный": "black",
            "зелёное": "green",
            "зеленое": "green",
            "зеленый": "green",
            "зелёный": "green",
        }

        selection = aliases.get(
            selection,
            selection,
        )

        if selection not in {
            "red",
            "black",
            "green",
        }:
            raise ValueError(
                "Invalid roulette selection."
            )

        amount = Decimal(str(bet))

        if amount <= 0:
            raise ValueError(
                "Bet amount must be greater than zero."
            )

        if await self.economy.get_balance(user_id) < amount:
            raise ValueError(
                "Insufficient balance."
            )

        game = await self.create(
            game_type="roulette",
            creator_id=user_id,
            chat_id=chat_id,
        )

        await self.join(
            game_id=game.id,
            user_id=user_id,
            bet=amount,
        )

        await self.place_bet(
            game_id=game.id,
            user_id=user_id,
            amount=amount,
            bet_type="color",
            selection=selection,
        )

        await self.repository.start_game(game.id)

        number = random.randint(0, 36)

        if number == 0:
            color = "green"
        elif number in {
            1, 3, 5, 7, 9, 12, 14, 16,
            18, 19, 21, 23, 25, 27, 30,
            32, 34, 36,
        }:
            color = "red"
        else:
            color = "black"

        won = color == selection

        multiplier = (
            Decimal("14.00")
            if selection == "green"
            else Decimal("1.90")
        )

        payout = (
            amount * multiplier
            if won
            else Decimal("0.00")
        )

        await self.repository.set_player_result(
            game_id=game.id,
            user_id=user_id,
            result="winner" if won else "loser",
            payout=payout,
        )

        if won:
            await self._payout(
                user_id=user_id,
                amount=payout,
                source="game:roulette",
                reference_id=game.round_id,
            )

        await self.repository.finish_game(
            game.id,
            winner_id=user_id if won else None,
        )

        return {
            "game_id": game.id,
            "game_type": "roulette",
            "number": number,
            "color": color,
            "selection": selection,
            "bet": amount,
            "won": won,
            "payout": payout,
        }

    # ========================================================================
    # DUEL
    # ========================================================================

    async def duel(
        self,
        *,
        creator_id: int,
        opponent_id: int,
        chat_id: int | None,
        bet: Decimal | int | float | str,
    ) -> dict[str, Any]:
        if creator_id == opponent_id:
            raise ValueError(
                "You cannot duel yourself."
            )

        amount = Decimal(str(bet))

        if amount <= 0:
            raise ValueError(
                "Duel bet must be greater than zero."
            )

        if await self.economy.get_balance(creator_id) < amount:
            raise ValueError(
                "Creator has insufficient balance."
            )

        if await self.economy.get_balance(opponent_id) < amount:
            raise ValueError(
                "Opponent has insufficient balance."
            )

        game = await self.create(
            game_type="duel",
            creator_id=creator_id,
            chat_id=chat_id,
        )

        await self.join(
            game_id=game.id,
            user_id=creator_id,
            bet=amount,
        )

        await self.join(
            game_id=game.id,
            user_id=opponent_id,
            bet=amount,
        )

        await self.place_bet(
            game_id=game.id,
            user_id=creator_id,
            amount=amount,
            bet_type="duel",
        )

        try:
            await self.place_bet(
                game_id=game.id,
                user_id=opponent_id,
                amount=amount,
                bet_type="duel",
            )
        except Exception:
            await self.cancel(game.id)
            raise

        await self.repository.start_game(game.id)

        winner_id = random.choice([
            creator_id,
            opponent_id,
        ])

        loser_id = (
            opponent_id
            if winner_id == creator_id
            else creator_id
        )

        winner_payout = (
            amount + amount * Decimal("0.50")
        )

        await self.repository.set_player_result(
            game_id=game.id,
            user_id=winner_id,
            result="winner",
            payout=winner_payout,
        )

        await self.repository.set_player_result(
            game_id=game.id,
            user_id=loser_id,
            result="loser",
            payout=Decimal("0.00"),
        )

        await self._payout(
            user_id=winner_id,
            amount=winner_payout,
            source="game:duel",
            reference_id=game.round_id,
        )

        await self.repository.finish_game(
            game.id,
            winner_id=winner_id,
        )

        return {
            "game_id": game.id,
            "game_type": "duel",
            "winner_id": winner_id,
            "loser_id": loser_id,
            "bet": amount,
            "winner_payout": winner_payout,
            "loser_payout": Decimal("0.00"),
        }

    # ========================================================================
    # RESULT
    # ========================================================================

    async def finish(
        self,
        *,
        game_id: int,
        winner_id: int | None = None,
    ) -> Game:
        game = await self.repository.finish_game(
            game_id,
            winner_id=winner_id,
        )

        if game is None:
            raise ValueError(
                "Game does not exist."
            )

        return game