from __future__ import annotations
from datetime import datetime
import asyncio
import random
from decimal import Decimal, InvalidOperation
from typing import Any, Sequence

from app.database.models.games import Game, GamePlayer
from app.database.repositories.economy import EconomyRepository
from app.database.repositories.games import GamesRepository


class GamesService:
    """
    Бизнес-логика игровой системы.

    Важные правила финансовой безопасности:

    1. Каждая ставка получает отдельный reference_id.
    2. Каждая выплата получает отдельный reference_id.
    3. Повторная ставка не должна списывать деньги повторно.
    4. Повторная выплата не должна создавать новые деньги.
    5. Все изменения выполняются в рамках текущей SQLAlchemy-сессии.
    6. Commit/rollback выполняет DatabaseMiddleware.
    7. При ошибке после списания НЕ выполняется ручной refund:
       транзакция целиком откатывается middleware.
    8. Внутри одного процесса конкурентные игровые операции
       сериализуются через asyncio.Lock.

    Важно:
        asyncio.Lock защищает от race condition внутри одного
        запущенного процесса бота.

        Для текущей архитектуры проекта (один процесс Python,
        локальная SQLite/PostgreSQL и ~250 пользователей) этого
        достаточно.
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

    _BET_TYPES = {
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
        Привести сумму к Decimal(0.01) и проверить её.

        Никогда не используем float напрямую для финансовых операций.
        Если float всё же пришёл от вызывающего кода, он сначала
        преобразуется через str().
        """

        try:
            value = Decimal(str(amount))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError(
                "Invalid bet amount."
            ) from exc

        if not value.is_finite():
            raise ValueError(
                "Bet amount must be finite."
            )

        try:
            value = value.quantize(
                Decimal("0.01")
            )
        except InvalidOperation as exc:
            raise ValueError(
                "Invalid bet amount."
            ) from exc

        if value <= 0:
            raise ValueError(
                "Bet amount must be greater than zero."
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
    def _validate_bet_type(
        cls,
        bet_type: str,
    ) -> str:
        if not isinstance(
            bet_type,
            str,
        ):
            raise ValueError(
                "Bet type must be a string."
            )

        bet_type = bet_type.strip().lower()

        if bet_type not in cls._BET_TYPES:
            raise ValueError(
                f"Unsupported bet type: {bet_type}"
            )

        return bet_type

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
        pot: Decimal | int | float | str = Decimal(
            "0.00"
        ),
        game_data: dict[str, Any] | None = None,
    ) -> Game:
        """
        Создать игру.

        Проверка active game и создание выполняются
        под одним process-level lock.

        Это закрывает race condition:

            request A -> get_active_game()
            request B -> get_active_game()
            request A -> create_game()
            request B -> create_game()

        При одном процессе бота второй запрос будет ждать lock.
        """

        game_type = (
            game_type.strip().lower()
        )

        if game_type not in self.GAME_TYPES:
            raise ValueError(
                f"Unsupported game type: {game_type}"
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
        existing = (
            await self.repository.get_active_game(
                game_type=game_type,
                creator_id=creator_id,
                chat_id=chat_id,
            )
        )

        if existing is not None:
            raise ValueError(
                "User already has an active game "
                "of this type."
            )

        return await self.repository.create_game(
            game_type=game_type,
            creator_id=creator_id,
            chat_id=chat_id,
            pot=self._decimal(pot),
            game_data=game_data,
        )

    async def cancel(
    self,
    game_id: int,
) -> Game:
    """
    Безопасно отменить игру.

    Возвращает игрокам все поставленные деньги,
    синхронизирует результаты GamePlayer/GameBet
    и переводит игру в cancelled.

    Все изменения выполняются в одной transaction.
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

            refund_reference = self._refund_reference(
                game.round_id,
                bet.user_id,
            )

            await self._payout(
                user_id=bet.user_id,
                amount=amount,
                source=f"game:{game.game_type}:refund",
                reference_id=refund_reference,
            )

            player = await self.repository.get_player(
                game_id=game.id,
                user_id=bet.user_id,
            )

            if player is not None:
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
        bet: Decimal | int | float | str = Decimal(
            "0.00"
        ),
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

        if game.status not in {
            "created",
            "waiting",
        }:
            raise ValueError(
                "Game is no longer accepting players."
            )

        existing = (
            await self.repository.get_player(
                game_id=game_id,
                user_id=user_id,
            )
        )

        if existing is not None:
            return existing

        normalized_bet = Decimal(
            "0.00"
        )

        if self._decimal(bet) > 0:
            normalized_bet = self._normalize_amount(
                bet
            )

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

        EconomyRepository отвечает за идемпотентность
        reference_id.
        """

        amount = self._decimal(amount)

        if amount <= 0:
            return

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
            3. Проверка reference_id через EconomyRepository.
            4. Списание денег.
            5. Создание GameBet.
            6. Увеличение pot.

        Всё находится в одной SQLAlchemy transaction.

        Если любой шаг после списания падает,
        DatabaseMiddleware откатит всю транзакцию.
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

        # --------------------------------------------------------------------
        # IDEMPOTENCY
        # --------------------------------------------------------------------

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

            return existing_bet

        reference_id = self._bet_reference(
            game.round_id,
            user_id,
        )

        # --------------------------------------------------------------------
        # CHARGE
        # --------------------------------------------------------------------

        transaction = (
            await self.economy.remove_balance(
                user_id=user_id,
                amount=amount,
                transaction_type="game_bet",
                source=f"game:{game.game_type}:bet",
                reference_id=reference_id,
            )
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
                "Existing game transaction does not match "
                "the requested bet amount."
            )

        # --------------------------------------------------------------------
        # CREATE BET
        # --------------------------------------------------------------------

        bet = await self.repository.create_bet(
            game_id=game_id,
            user_id=user_id,
            amount=amount,
            bet_type=bet_type,
            selection=selection,
        )

        # --------------------------------------------------------------------
        # UPDATE POT
        # --------------------------------------------------------------------

        current_pot = self._decimal(
            game.pot
        )

        updated_game = (
            await self.repository.update_game(
                game.id,
                pot=current_pot + amount,
            )
        )

        if updated_game is None:
            raise RuntimeError(
                "Game disappeared while placing a bet."
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

        if (
            target is not None
            and not 1 <= target <= sides
        ):
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
                bet_type="dice",
                selection=(
                    str(target)
                    if target is not None
                    else "high"
                ),
            )

            await self.repository.start_game(
                game.id
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
                    reference_id=(
                        self._payout_reference(
                            game.round_id,
                            "dice",
                            user_id,
                        )
                    ),
                )

            await self.repository.finish_game(
                game.id,
                winner_id=(
                    user_id
                    if won
                    else None
                ),
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
                bet_type="coinflip",
                selection=selection,
            )

            await self.repository.start_game(
                game.id
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
                    reference_id=(
                        self._payout_reference(
                            game.round_id,
                            "coinflip",
                            user_id,
                        )
                    ),
                )

            await self.repository.finish_game(
                game.id,
                winner_id=(
                    user_id
                    if won
                    else None
                ),
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
            "черное": "black",
            "чёрное": "black",
            "черный": "black",
            "зелёное": "green",
            "зеленое": "green",
            "зеленый": "green",
            "зелёный": "green",
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
                bet_type="color",
                selection=selection,
            )

            await self.repository.start_game(
                game.id
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
                    reference_id=(
                        self._payout_reference(
                            game.round_id,
                            "roulette",
                            user_id,
                        )
                    ),
                )

            await self.repository.finish_game(
                game.id,
                winner_id=(
                    user_id
                    if won
                    else None
                ),
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

            await self.repository.start_game(
                game.id
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

            while player_value < 17:
                player_cards.append(
                    draw_card()
                )
                player_value = hand_value(
                    player_cards
                )

            while dealer_value < 17:
                dealer_cards.append(
                    draw_card()
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

            payout = amount * multiplier

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
                    reference_id=(
                        self._payout_reference(
                            game.round_id,
                            "blackjack",
                            user_id,
                        )
                    ),
                )

            await self.repository.finish_game(
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
                game_data=None,
            )

            # ----------------------------------------------------------------
            # BOTH PLAYERS ARE PART OF THE SAME TRANSACTION
            # ----------------------------------------------------------------
            #
            # Если списание второго игрока не удалось,
            # исключение поднимается наверх.
            #
            # DatabaseMiddleware выполнит rollback,
            # поэтому списание первого игрока тоже исчезнет.
            #
            # Никакого ручного refund здесь НЕ делаем.
            # ----------------------------------------------------------------

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

            await self.repository.start_game(
                game.id
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
                reference_id=(
                    self._payout_reference(
                        game.round_id,
                        "duel",
                        winner_id,
                    )
                ),
            )

            await self.repository.finish_game(
                game.id,
                winner_id=winner_id,
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