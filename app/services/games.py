from __future__ import annotations

import asyncio
import random
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Sequence

from app.database.models.games import Game, GamePlayer
from app.database.repositories.economy import EconomyRepository
from app.database.repositories.games import GamesRepository


class GamesService:
    """
    Бизнес-логика игровой системы.

    Финансовые правила:

    1. Каждая ставка получает собственный reference_id.
    2. Каждая выплата получает собственный reference_id.
    3. Повторная ставка не списывает деньги повторно.
    4. Повторная выплата не начисляет деньги повторно.
    5. Все изменения выполняются в рамках текущей SQLAlchemy-сессии.
    6. Commit/rollback выполняет DatabaseMiddleware.
    7. При ошибке после списания ручной refund НЕ выполняется:
       вся transaction откатывается middleware.
    8. Конкурентные игровые операции сериализуются через asyncio.Lock.

    Архитектура рассчитана на один процесс Python.
    Для текущего проекта этого достаточно.
    """

    ACTIVE_STATUSES = {
        "created",
        "waiting",
        "active",
    }

    JOINABLE_STATUSES = {
        "created",
        "waiting",
    }

    GAME_TYPES = {
        "roulette",
        "blackjack",
        "dice",
        "duel",
        "coinflip",
    }

    BET_TYPES = {
        "dice",
        "coinflip",
        "color",
        "blackjack",
        "duel",
    }

    _game_lock = asyncio.Lock()

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

    @staticmethod
    def _normalize_amount(
        amount: Decimal | int | float | str,
    ) -> Decimal:
        """
        Привести денежную сумму к Decimal с двумя знаками.
        """

        try:
            value = Decimal(str(amount))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError(
                "Invalid amount."
            ) from exc

        if not value.is_finite():
            raise ValueError(
                "Amount must be finite."
            )

        try:
            value = value.quantize(
                Decimal("0.01")
            )
        except InvalidOperation as exc:
            raise ValueError(
                "Invalid amount."
            ) from exc

        if value <= 0:
            raise ValueError(
                "Amount must be greater than zero."
            )

        return value

    @staticmethod
    def _decimal(
        value: Decimal | int | float | str,
    ) -> Decimal:
        """
        Безопасно преобразовать значение БД/модели в Decimal.
        """

        try:
            result = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise RuntimeError(
                "Invalid decimal value."
            ) from exc

        if not result.is_finite():
            raise RuntimeError(
                "Decimal value must be finite."
            )

        return result

    @staticmethod
    def _bet_reference(
        round_id: str,
        user_id: int,
    ) -> str:
        return (
            f"{round_id}:bet:{user_id}"
        )

    @staticmethod
    def _payout_reference(
        round_id: str,
        game_type: str,
        user_id: int,
    ) -> str:
        return (
            f"{round_id}:payout:"
            f"{game_type}:{user_id}"
        )

    @staticmethod
    def _refund_reference(
        round_id: str,
        user_id: int,
    ) -> str:
        return (
            f"{round_id}:refund:{user_id}"
        )

    @classmethod
    def _validate_game_type(
        cls,
        game_type: str,
    ) -> str:
        if not isinstance(game_type, str):
            raise ValueError(
                "Game type must be a string."
            )

        game_type = game_type.strip().lower()

        if game_type not in cls.GAME_TYPES:
            raise ValueError(
                f"Unsupported game type: {game_type}"
            )

        return game_type

    @classmethod
    def _validate_bet_type(
        cls,
        bet_type: str,
    ) -> str:
        if not isinstance(bet_type, str):
            raise ValueError(
                "Bet type must be a string."
            )

        bet_type = bet_type.strip().lower()

        if bet_type not in cls.BET_TYPES:
            raise ValueError(
                f"Unsupported bet type: {bet_type}"
            )

        return bet_type

    @staticmethod
    def _normalize_selection(
        selection: str | None,
    ) -> str | None:
        if selection is None:
            return None

        if not isinstance(selection, str):
            raise ValueError(
                "Selection must be a string."
            )

        selection = selection.strip().lower()

        if not selection:
            raise ValueError(
                "Selection cannot be empty."
            )

        return selection

    # ========================================================================
    # GAME
    # ========================================================================

    async def get_game(
        self,
        game_id: int,
    ) -> Game | None:
        return await self.repository.get_game(
            game_id
        )

    async def create(
        self,
        *,
        game_type: str,
        creator_id: int,
        chat_id: int | None = None,
        pot: Decimal | int | float | str = Decimal("0.00"),
        game_data: dict[str, Any] | None = None,
    ) -> Game:
        """
        Создать игру.

        Проверка существующей активной игры и создание
        выполняются под одним lock.
        """

        game_type = self._validate_game_type(
            game_type
        )

        async with self._game_lock:
            return await self._create_unlocked(
                game_type=game_type,
                creator_id=creator_id,
                chat_id=chat_id,
                pot=pot,
                game_data=game_data,
            )

    async def _create_unlocked(
        self,
        *,
        game_type: str,
        creator_id: int,
        chat_id: int | None,
        pot: Decimal | int | float | str,
        game_data: dict[str, Any] | None,
    ) -> Game:
        game_type = self._validate_game_type(
            game_type
        )

        pot_value = self._decimal(pot)

        if pot_value < 0:
            raise ValueError(
                "Game pot cannot be negative."
            )

        existing = await self.repository.get_active_game(
            game_type=game_type,
            creator_id=creator_id,
            chat_id=chat_id,
        )

        if existing is not None:
            raise ValueError(
                "User already has an active game "
                "of this type."
            )

        game = await self.repository.create_game(
            game_type=game_type,
            creator_id=creator_id,
            chat_id=chat_id,
            pot=pot_value,
            game_data=game_data,
        )

        if game is None:
            raise RuntimeError(
                "Failed to create game."
            )

        return game

    async def cancel(
        self,
        game_id: int,
    ) -> Game:
        """
        Отменить игру и вернуть все фактически поставленные ставки.

        Все изменения находятся в одной transaction.
        """

        async with self._game_lock:
            game = await self.repository.get_game(
                game_id
            )

            if game is None:
                raise ValueError(
                    "Game does not exist."
                )

            if game.status not in self.ACTIVE_STATUSES:
                raise ValueError(
                    "Only active games can be cancelled."
                )

            bets = await self.repository.get_game_bets(
                game_id
            )

            for bet in bets:
                amount = self._decimal(
                    bet.amount
                )

                if amount <= 0:
                    continue

                refund_reference = (
                    self._refund_reference(
                        game.round_id,
                        bet.user_id,
                    )
                )

                await self._payout(
                    user_id=bet.user_id,
                    amount=amount,
                    source=(
                        f"game:{game.game_type}:refund"
                    ),
                    reference_id=refund_reference,
                )

                player = await self.repository.get_player(
                    game_id=game.id,
                    user_id=bet.user_id,
                )

                if player is None:
                    raise RuntimeError(
                        "GameBet exists without "
                        "corresponding GamePlayer."
                    )

                player.result = "cancelled"
                player.payout = amount
                bet.payout = amount

            updated_game = await self.repository.update_game(
                game.id,
                pot=Decimal("0.00"),
                status="cancelled",
                finished_at=datetime.now(),
            )

            if updated_game is None:
                raise RuntimeError(
                    "Game disappeared while cancelling."
                )

            return updated_game

    async def join(
        self,
        *,
        game_id: int,
        user_id: int,
        bet: Decimal | int | float | str = Decimal("0.00"),
    ) -> GamePlayer:
        async with self._game_lock:
            return await self._join_unlocked(
                game_id=game_id,
                user_id=user_id,
                bet=bet,
            )

    async def _join_unlocked(
        self,
        *,
        game_id: int,
        user_id: int,
        bet: Decimal | int | float | str,
    ) -> GamePlayer:
        game = await self.repository.get_game(
            game_id
        )

        if game is None:
            raise ValueError(
                "Game does not exist."
            )

        if game.status not in self.JOINABLE_STATUSES:
            raise ValueError(
                "Game is no longer accepting players."
            )

        raw_bet = self._decimal(bet)

        if raw_bet < 0:
            raise ValueError(
                "Player bet cannot be negative."
            )

        normalized_bet = (
            Decimal("0.00")
            if raw_bet == 0
            else self._normalize_amount(raw_bet)
        )

        existing = await self.repository.get_player(
            game_id=game_id,
            user_id=user_id,
        )

        if existing is not None:
            existing_bet = self._decimal(
                existing.bet
            )

            if existing_bet != normalized_bet:
                raise ValueError(
                    "Player is already participating "
                    "with a different bet."
                )

            return existing

        return await self.repository.add_player(
            game_id=game_id,
            user_id=user_id,
            bet=normalized_bet,
        )

    async def players(
        self,
        game_id: int,
    ) -> Sequence[GamePlayer]:
        return await self.repository.get_game_players(
            game_id
        )

    # ========================================================================
    # ECONOMY
    # ========================================================================

    async def _payout(
        self,
        *,
        user_id: int,
        amount: Decimal,
        source: str,
        reference_id: str,
    ) -> None:
        """
        Начислить выплату.

        EconomyRepository обеспечивает идемпотентность
        по reference_id.
        """

        amount = self._decimal(amount)

        if amount <= 0:
            return

        if not reference_id:
            raise ValueError(
                "Payout reference_id cannot be empty."
            )

        await self.economy.add_balance(
            user_id=user_id,
            amount=amount,
            transaction_type="game_payout",
            source=source,
            reference_id=reference_id,
        )

    # ========================================================================
    # BET
    # ========================================================================

    async def place_bet(
        self,
        *,
        game_id: int,
        user_id: int,
        amount: Decimal | int | float | str,
        bet_type: str,
        selection: str | None = None,
    ) -> GamePlayer:
        """
        Поставить деньги в игре.

        Последовательность:

            1. Проверка игры.
            2. Проверка существующей ставки.
            3. Списание денег.
            4. Создание GameBet.
            5. Обновление pot.

        Commit/rollback выполняется middleware.
        """

        async with self._game_lock:
            return await self._place_bet_unlocked(
                game_id=game_id,
                user_id=user_id,
                amount=amount,
                bet_type=bet_type,
                selection=selection,
            )

    async def _place_bet_unlocked(
        self,
        *,
        game_id: int,
        user_id: int,
        amount: Decimal | int | float | str,
        bet_type: str,
        selection: str | None,
    ) -> GamePlayer:
        game = await self.repository.get_game(
            game_id
        )

        if game is None:
            raise ValueError(
                "Game does not exist."
            )

        if game.status not in self.ACTIVE_STATUSES:
            raise ValueError(
                "Game is not active."
            )

        amount = self._normalize_amount(
            amount
        )

        bet_type = self._validate_bet_type(
            bet_type
        )

        selection = self._normalize_selection(
            selection
        )

        existing_bet = (
            await self.repository.get_user_bet(
                game_id=game_id,
                user_id=user_id,
            )
        )

        if existing_bet is not None:
            existing_amount = self._decimal(
                existing_bet.amount
            )

            if existing_amount != amount:
                raise ValueError(
                    "A different bet already exists "
                    "for this game."
                )

            if existing_bet.bet_type != bet_type:
                raise ValueError(
                    "A different bet type already exists "
                    "for this game."
                )

            if existing_bet.selection != selection:
                raise ValueError(
                    "A different bet selection already exists "
                    "for this game."
                )

            player = await self.repository.get_player(
                game_id=game_id,
                user_id=user_id,
            )

            if player is None:
                raise RuntimeError(
                    "GameBet exists without "
                    "corresponding GamePlayer."
                )

            return player

        reference_id = self._bet_reference(
            game.round_id,
            user_id,
        )

        transaction = await self.economy.remove_balance(
            user_id=user_id,
            amount=amount,
            transaction_type="game_bet",
            source=f"game:{game.game_type}:bet",
            reference_id=reference_id,
        )

        if transaction is None:
            raise ValueError(
                "Insufficient balance."
            )

        transaction_amount = self._decimal(
            transaction.amount
        )

        if transaction_amount != -amount:
            raise RuntimeError(
                "Game transaction amount does not match "
                "the requested bet."
            )

        bet = await self.repository.create_bet(
            game_id=game_id,
            user_id=user_id,
            amount=amount,
            bet_type=bet_type,
            selection=selection,
        )

        if bet is None:
            raise RuntimeError(
                "Failed to create game bet."
            )

        current_pot = self._decimal(
            game.pot
        )

        updated_game = await self.repository.update_game(
            game.id,
            pot=current_pot + amount,
        )

        if updated_game is None:
            raise RuntimeError(
                "Game disappeared while placing a bet."
            )

        player = await self.repository.get_player(
            game_id=game_id,
            user_id=user_id,
        )

        if player is None:
            raise RuntimeError(
                "GameBet was created without "
                "corresponding GamePlayer."
            )

        return player

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
        if not isinstance(sides, int):
            raise ValueError(
                "Dice sides must be an integer."
            )

        if sides < 2 or sides > 100:
            raise ValueError(
                "Dice sides must be between 2 and 100."
            )

        if target is not None:
            if not isinstance(target, int):
                raise ValueError(
                    "Dice target must be an integer."
                )

            if not 1 <= target <= sides:
                raise ValueError(
                    "Dice target is outside "
                    "the dice range."
                )

        amount = self._normalize_amount(
            bet
        )

        async with self._game_lock:
            game = await self._create_unlocked(
                game_type="dice",
                creator_id=user_id,
                chat_id=chat_id,
                pot=Decimal("0.00"),
                game_data={
                    "sides": sides,
                    "target": target,
                },
            )

            await self._join_unlocked(
                game_id=game.id,
                user_id=user_id,
                bet=amount,
            )

            await self._place_bet_unlocked(
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

            started_game = await self.repository.start_game(
                game.id
            )

            if started_game is None:
                raise RuntimeError(
                    "Failed to start dice game."
                )

            roll = random.randint(
                1,
                sides,
            )

            won = (
                roll == target
                if target is not None
                else roll > sides // 2
            )

            if target is not None:
                payout = (
                    amount * Decimal(sides)
                    if won
                    else Decimal("0.00")
                )
            else:
                payout = (
                    amount * Decimal("1.90")
                    if won
                    else Decimal("0.00")
                )

            await self.repository.set_player_result(
                game_id=game.id,
                user_id=user_id,
                result=(
                    "winner"
                    if won
                    else "loser"
                ),
                payout=payout,
            )

            if won:
                await self._payout(
                    user_id=user_id,
                    amount=payout,
                    source="game:dice",
                    reference_id=self._payout_reference(
                        game.round_id,
                        "dice",
                        user_id,
                    ),
                )

            finished_game = await self.repository.finish_game(
                game.id,
                winner_id=(
                    user_id
                    if won
                    else None
                ),
            )

            if finished_game is None:
                raise RuntimeError(
                    "Failed to finish dice game."
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

        amount = self._normalize_amount(
            bet
        )

        async with self._game_lock:
            game = await self._create_unlocked(
                game_type="coinflip",
                creator_id=user_id,
                chat_id=chat_id,
                pot=Decimal("0.00"),
                game_data={
                    "selection": selection,
                },
            )

            await self._join_unlocked(
                game_id=game.id,
                user_id=user_id,
                bet=amount,
            )

            await self._place_bet_unlocked(
                game_id=game.id,
                user_id=user_id,
                amount=amount,
                bet_type="coinflip",
                selection=selection,
            )

            started_game = await self.repository.start_game(
                game.id
            )

            if started_game is None:
                raise RuntimeError(
                    "Failed to start coinflip game."
                )

            result = random.choice(
                (
                    "heads",
                    "tails",
                )
            )

            won = result == selection

            payout = (
                amount * Decimal("1.90")
                if won
                else Decimal("0.00")
            )

            await self.repository.set_player_result(
                game_id=game.id,
                user_id=user_id,
                result=(
                    "winner"
                    if won
                    else "loser"
                ),
                payout=payout,
            )

            if won:
                await self._payout(
                    user_id=user_id,
                    amount=payout,
                    source="game:coinflip",
                    reference_id=self._payout_reference(
                        game.round_id,
                        "coinflip",
                        user_id,
                    ),
                )

            finished_game = await self.repository.finish_game(
                game.id,
                winner_id=(
                    user_id
                    if won
                    else None
                ),
            )

            if finished_game is None:
                raise RuntimeError(
                    "Failed to finish coinflip game."
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
        aliases = {
            "красное": "red",
            "красный": "red",
            "красный цвет": "red",
            "черное": "black",
            "чёрное": "black",
            "черный": "black",
            "чёрный": "black",
            "черный цвет": "black",
            "чёрный цвет": "black",
            "зелёное": "green",
            "зеленое": "green",
            "зеленый": "green",
            "зелёный": "green",
            "зеро": "green",
            "zero": "green",
        }

        selection = aliases.get(
            selection.strip().lower(),
            selection.strip().lower(),
        )

        if selection not in {
            "red",
            "black",
            "green",
        }:
            raise ValueError(
                "Invalid roulette selection."
            )

        amount = self._normalize_amount(
            bet
        )

        async with self._game_lock:
            game = await self._create_unlocked(
                game_type="roulette",
                creator_id=user_id,
                chat_id=chat_id,
                pot=Decimal("0.00"),
                game_data={
                    "selection": selection,
                },
            )

            await self._join_unlocked(
                game_id=game.id,
                user_id=user_id,
                bet=amount,
            )

            await self._place_bet_unlocked(
                game_id=game.id,
                user_id=user_id,
                amount=amount,
                bet_type="color",
                selection=selection,
            )

            started_game = await self.repository.start_game(
                game.id
            )

            if started_game is None:
                raise RuntimeError(
                    "Failed to start roulette game."
                )

            number = random.randint(
                0,
                36,
            )

            if number == 0:
                color = "green"

            elif number in {
                1, 3, 5, 7, 9,
                12, 14, 16, 18,
                19, 21, 23, 25,
                27, 30, 32, 34, 36,
            }:
                color = "red"

            else:
                color = "black"

            won = color == selection

            # Возврат ставки + выигрыш:
            #
            # red/black:
            #     1.90x
            #
            # green:
            #     14x
            #
            # Эти коэффициенты являются игровой экономикой проекта,
            # а не попыткой имитировать официальный европейский roulette payout.
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
                result=(
                    "winner"
                    if won
                    else "loser"
                ),
                payout=payout,
            )

            if won:
                await self._payout(
                    user_id=user_id,
                    amount=payout,
                    source="game:roulette",
                    reference_id=self._payout_reference(
                        game.round_id,
                        "roulette",
                        user_id,
                    ),
                )

            finished_game = await self.repository.finish_game(
                game.id,
                winner_id=(
                    user_id
                    if won
                    else None
                ),
            )

            if finished_game is None:
                raise RuntimeError(
                    "Failed to finish roulette game."
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
    # BLACKJACK
    # ========================================================================

    async def blackjack(
        self,
        *,
        user_id: int,
        chat_id: int | None,
        bet: Decimal | int | float | str,
    ) -> dict[str, Any]:
        amount = self._normalize_amount(
            bet
        )

        async with self._game_lock:
            game = await self._create_unlocked(
                game_type="blackjack",
                creator_id=user_id,
                chat_id=chat_id,
                pot=Decimal("0.00"),
                game_data=None,
            )

            await self._join_unlocked(
                game_id=game.id,
                user_id=user_id,
                bet=amount,
            )

            await self._place_bet_unlocked(
                game_id=game.id,
                user_id=user_id,
                amount=amount,
                bet_type="blackjack",
            )

            started_game = await self.repository.start_game(
                game.id
            )

            if started_game is None:
                raise RuntimeError(
                    "Failed to start blackjack game."
                )

            def draw_card() -> int:
                card = random.randint(
                    1,
                    13,
                )

                return min(
                    card,
                    10,
                )

            def hand_value(
                cards: list[int],
            ) -> int:
                value = sum(cards)
                aces = cards.count(1)

                while (
                    aces
                    and value + 10 <= 21
                ):
                    value += 10
                    aces -= 1

                return value

            player_cards = [
                draw_card(),
                draw_card(),
            ]

            dealer_cards = [
                draw_card(),
                draw_card(),
            ]

            player_value = hand_value(
                player_cards
            )

            dealer_value = hand_value(
                dealer_cards
            )

            player_blackjack = (
                len(player_cards) == 2
                and player_value == 21
            )

            dealer_blackjack = (
                len(dealer_cards) == 2
                and dealer_value == 21
            )

            if not player_blackjack:
                while player_value < 17:
                    player_cards.append(
                        draw_card()
                    )

                    player_value = hand_value(
                        player_cards
                    )

            while (
                not dealer_blackjack
                and dealer_value < 17
            ):
                dealer_cards.append(
                    draw_card()
                )

                dealer_value = hand_value(
                    dealer_cards
                )

            if (
                player_blackjack
                and not dealer_blackjack
            ):
                result = "blackjack"
                multiplier = Decimal("2.50")

            elif player_value > 21:
                result = "loser"
                multiplier = Decimal("0.00")

            elif dealer_value > 21:
                result = "winner"
                multiplier = Decimal("1.90")

            elif player_value > dealer_value:
                result = "winner"
                multiplier = Decimal("1.90")

            elif player_value < dealer_value:
                result = "loser"
                multiplier = Decimal("0.00")

            else:
                result = "draw"
                multiplier = Decimal("1.00")

            payout = (
                amount * multiplier
            )

            await self.repository.set_player_result(
                game_id=game.id,
                user_id=user_id,
                result=result,
                payout=payout,
            )

            if payout > 0:
                await self._payout(
                    user_id=user_id,
                    amount=payout,
                    source="game:blackjack",
                    reference_id=self._payout_reference(
                        game.round_id,
                        "blackjack",
                        user_id,
                    ),
                )

            finished_game = await self.repository.finish_game(
                game.id,
                winner_id=(
                    user_id
                    if result in {
                        "winner",
                        "blackjack",
                    }
                    else None
                ),
            )

            if finished_game is None:
                raise RuntimeError(
                    "Failed to finish blackjack game."
                )

            return {
                "game_id": game.id,
                "game_type": "blackjack",
                "player_cards": player_cards,
                "dealer_cards": dealer_cards,
                "player_value": player_value,
                "dealer_value": dealer_value,
                "result": result,
                "bet": amount,
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

        amount = self._normalize_amount(
            bet
        )

        async with self._game_lock:
            game = await self._create_unlocked(
                game_type="duel",
                creator_id=creator_id,
                chat_id=chat_id,
                pot=Decimal("0.00"),
                game_data={
                    "creator_id": creator_id,
                    "opponent_id": opponent_id,
                    "bet": str(amount),
                },
            )

            # ---------------------------------------------------------------
            # CREATOR
            # ---------------------------------------------------------------

            await self._join_unlocked(
                game_id=game.id,
                user_id=creator_id,
                bet=amount,
            )

            await self._place_bet_unlocked(
                game_id=game.id,
                user_id=creator_id,
                amount=amount,
                bet_type="duel",
            )

            # ---------------------------------------------------------------
            # OPPONENT
            # ---------------------------------------------------------------

            await self._join_unlocked(
                game_id=game.id,
                user_id=opponent_id,
                bet=amount,
            )

            await self._place_bet_unlocked(
                game_id=game.id,
                user_id=opponent_id,
                amount=amount,
                bet_type="duel",
            )

            # ---------------------------------------------------------------
            # START
            # ---------------------------------------------------------------

            started_game = await self.repository.start_game(
                game.id
            )

            if started_game is None:
                raise RuntimeError(
                    "Failed to start duel game."
                )

            winner_id, loser_id = random.choice(
                [
                    (
                        creator_id,
                        opponent_id,
                    ),
                    (
                        opponent_id,
                        creator_id,
                    ),
                ]
            )

            # Правило проекта:
            #
            # победитель получает:
            #   собственную ставку обратно
            #   + 50% ставки противника
            #
            # Итого:
            #   1.5 * bet
            winner_payout = (
                amount
                + amount * Decimal("0.50")
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
                reference_id=self._payout_reference(
                    game.round_id,
                    "duel",
                    winner_id,
                ),
            )

            finished_game = await self.repository.finish_game(
                game.id,
                winner_id=winner_id,
            )

            if finished_game is None:
                raise RuntimeError(
                    "Failed to finish duel game."
                )

            return {
                "game_id": game.id,
                "game_type": "duel",
                "creator_id": creator_id,
                "opponent_id": opponent_id,
                "winner_id": winner_id,
                "loser_id": loser_id,
                "bet": amount,
                "winner_payout": winner_payout,
            }