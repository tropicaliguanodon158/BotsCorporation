from __future__ import annotations

import random
from decimal import Decimal
from typing import Any, Sequence

from app.database.models.games import Game, GamePlayer
from app.database.repositories.economy import EconomyRepository
from app.database.repositories.games import GamesRepository


class GamesService:
    """
    Бизнес-логика игровых механик.

    Важные правила финансовой безопасности:

    1. Ставка и выплата имеют разные reference_id.
    2. Повторная выплата не должна создавать новые деньги.
    3. При ошибке после списания ставка возвращается.
    4. Предварительная проверка баланса не используется как
       гарантия достаточности средств.
    5. Реальная проверка баланса выполняется EconomyRepository.
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

    @staticmethod
    def _normalize_amount(
        amount: Decimal | int | float | str,
    ) -> Decimal:
        try:
            value = Decimal(str(amount))
        except Exception as exc:
            raise ValueError(
                "Invalid bet amount."
            ) from exc

        if not value.is_finite():
            raise ValueError(
                "Bet amount must be finite."
            )

        value = value.quantize(
            Decimal("0.01")
        )

        if value <= 0:
            raise ValueError(
                "Bet amount must be greater than zero."
            )

        return value

    @staticmethod
    def _bet_reference(
        round_id: str,
        user_id: int,
    ) -> str:
        return (
            f"{round_id}:bet:{user_id}"
        )

    @staticmethod
    def _rollback_reference(
        round_id: str,
        user_id: int,
    ) -> str:
        return (
            f"{round_id}:bet_rollback:{user_id}"
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
        game_type = (
            game_type.strip().lower()
        )

        if game_type not in self.GAME_TYPES:
            raise ValueError(
                f"Unsupported game type: {game_type}"
            )

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
            pot=pot,
            game_data=game_data,
        )

    async def cancel(
        self,
        game_id: int,
    ) -> Game:
        game = await self.repository.cancel_game(
            game_id
        )

        if game is None:
            raise ValueError(
                "Game does not exist."
            )

        return game

    async def join(
        self,
        *,
        game_id: int,
        user_id: int,
        bet: Decimal | int | float | str = Decimal(
            "0.00"
        ),
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

        return await self.repository.add_player(
            game_id=game_id,
            user_id=user_id,
            bet=bet,
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

    async def _charge(
        self,
        *,
        user_id: int,
        amount: Decimal,
        source: str,
        reference_id: str,
    ) -> None:
        amount = self._normalize_amount(
            amount
        )

        transaction = (
            await self.economy.remove_balance(
                user_id=user_id,
                amount=amount,
                transaction_type="game_bet",
                source=source,
                reference_id=reference_id,
            )
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
        if amount <= 0:
            return

        await self.economy.add_balance(
            user_id=user_id,
            amount=amount,
            transaction_type="game_payout",
            source=source,
            reference_id=reference_id,
        )

    async def _refund_bet(
        self,
        *,
        user_id: int,
        amount: Decimal,
        game: Game,
    ) -> None:
        """
        Возврат уже списанной ставки.

        Отдельный reference_id гарантирует, что возврат
        не будет спутан с исходным списанием.
        """

        await self._payout(
            user_id=user_id,
            amount=amount,
            source="game_bet_rollback",
            reference_id=self._rollback_reference(
                game.round_id,
                user_id,
            ),
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

        reference_id = self._bet_reference(
            game.round_id,
            user_id,
        )

        await self._charge(
            user_id=user_id,
            amount=amount,
            source=(
                f"game:{game.game_type}:bet"
            ),
            reference_id=reference_id,
        )

        try:
            bet = await self.repository.create_bet(
                game_id=game_id,
                user_id=user_id,
                amount=amount,
                bet_type=bet_type,
                selection=selection,
            )

            game.pot += amount

            await self.repository.update_game(
                game.id,
                pot=game.pot,
            )

            return bet

        except Exception:
            try:
                await self._refund_bet(
                    user_id=user_id,
                    amount=amount,
                    game=game,
                )
            except Exception:
                # Исходная ошибка важнее.
                # Если возврат тоже упал, внешний логгер
                # должен зафиксировать обе ошибки.
                raise

            raise

    # ========================================================================
    # VALIDATION
    # ========================================================================

    @staticmethod
    def _validate_bet(
        bet: Decimal | int | float | str,
    ) -> Decimal:
        try:
            amount = Decimal(str(bet))
        except Exception as exc:
            raise ValueError(
                "Invalid bet amount."
            ) from exc

        if not amount.is_finite():
            raise ValueError(
                "Bet amount must be finite."
            )

        amount = amount.quantize(
            Decimal("0.01")
        )

        if amount <= 0:
            raise ValueError(
                "Bet amount must be greater than zero."
            )

        return amount

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

        amount = self._validate_bet(
            bet
        )

        game = await self.create(
            game_type="dice",
            creator_id=user_id,
            chat_id=chat_id,
        )

        try:
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

        except Exception:
            raise

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

        amount = self._validate_bet(
            bet
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

        amount = self._validate_bet(
            bet
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
        amount = self._validate_bet(
            bet
        )

        game = await self.create(
            game_type="blackjack",
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

        amount = self._validate_bet(
            bet
        )

        game = await self.create(
            game_type="duel",
            creator_id=creator_id,
            chat_id=chat_id,
        )

        creator_charged = False
        opponent_charged = False

        try:
            await self.join(
                game_id=game.id,
                user_id=creator_id,
                bet=amount,
            )

            await self.place_bet(
                game_id=game.id,
                user_id=creator_id,
                amount=amount,
                bet_type="duel",
            )

            creator_charged = True

            await self.join(
                game_id=game.id,
                user_id=opponent_id,
                bet=amount,
            )

            await self.place_bet(
                game_id=game.id,
                user_id=opponent_id,
                amount=amount,
                bet_type="duel",
            )

            opponent_charged = True

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

        except Exception:

            # Если place_bet() уже создал собственный rollback,
            # повторно деньги здесь не возвращаем.

            # Если первая ставка была успешно списана,
            # но ошибка произошла до второй ставки,
            # возвращаем первую.

            if (
                creator_charged
                and not opponent_charged
            ):
                await self._refund_bet(
                    user_id=creator_id,
                    amount=amount,
                    game=game,
                )

            raise
