"""
Repository for game system.

Работает с:

    Game
        Игровая сессия.

    GamePlayer
        Участник игровой сессии.

    GameBet
        Отдельная ставка и её финансовый результат.

Repository отвечает только за работу с БД.

Игровая логика:
    roulette
    blackjack
    dice
    duel
    coinflip

будет находиться в services/games.py.
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.games import (
    Game,
    GameBet,
    GamePlayer,
)


class GamesRepository:
    """
    Репозиторий игровых сессий.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ========================================================================
    # GAMES
    # ========================================================================


    async def create_game(
        self,
        *,
        game_type: str,
        creator_id: int,
        chat_id: int | None = None,
        status: str = "created",
        pot: Decimal | int | float | str = Decimal("0.00"),
        game_data: dict[str, Any] | None = None,
        round_id: str | None = None,
    ) -> Game:
        """
        Создать игровую сессию.
        """
    
        game_type = game_type.strip()
    
        if not game_type:
            raise ValueError(
                "game_type cannot be empty."
            )
    
        pot = Decimal(str(pot))
    
        if pot < 0:
            raise ValueError(
                "Game pot cannot be negative."
            )
    
        if round_id is None:
            round_id = uuid4().hex
        else:
            round_id = round_id.strip()
    
            if not round_id:
                raise ValueError(
                    "round_id cannot be empty."
                )
    
        game_data_json: str | None = None
    
        if game_data is not None:
            game_data_json = json.dumps(
                game_data,
                ensure_ascii=False,
                default=str,
            )
    
        game = Game(
            game_type=game_type,
            status=status,
            chat_id=chat_id,
            creator_id=creator_id,
            pot=pot,
            game_data=game_data_json,
            round_id=round_id,
        )
    
        self.session.add(game)
    
        await self.session.flush()
    
        return game


    async def get_game(
        self,
        game_id: int,
    ) -> Game | None:
        """
        Получить игру по ID.
        """

        result = await self.session.execute(
            select(Game).where(
                Game.id == game_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_game_by_round_id(
        self,
        round_id: str,
    ) -> Game | None:
        """
        Получить игру по публичному идентификатору раунда.
        """

        result = await self.session.execute(
            select(Game).where(
                Game.round_id == round_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_active_game(
        self,
        *,
        game_type: str,
        creator_id: int | None = None,
        chat_id: int | None = None,
    ) -> Game | None:
        """
        Найти активную игру.

        Используется для предотвращения создания
        нескольких конфликтующих игровых сессий.
        """

        active_statuses = {
            "created",
            "waiting",
            "active",
        }

        query = select(Game).where(
            Game.game_type == game_type,
            Game.status.in_(active_statuses),
        )

        if creator_id is not None:
            query = query.where(
                Game.creator_id == creator_id,
            )

        if chat_id is not None:
            query = query.where(
                Game.chat_id == chat_id,
            )

        query = query.order_by(
            Game.created_at.desc(),
        )

        result = await self.session.execute(query)

        return result.scalars().first()

    async def get_chat_games(
        self,
        *,
        chat_id: int,
        game_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Game]:
        """
        Получить игры конкретного чата.
        """

        limit = max(1, min(limit, 1000))
        offset = max(0, offset)

        query = select(Game).where(
            Game.chat_id == chat_id,
        )

        if game_type is not None:
            query = query.where(
                Game.game_type == game_type,
            )

        if status is not None:
            query = query.where(
                Game.status == status,
            )

        query = (
            query
            .order_by(
                Game.created_at.desc(),
                Game.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    async def update_game(
        self,
        game_id: int,
        **values: object,
    ) -> Game | None:
        """
        Изменить состояние игры.

        Предназначено для services/games.py.
        """

        allowed_fields = {
            "status",
            "winner_id",
            "pot",
            "game_data",
            "round_id",
            "started_at",
            "finished_at",
        }

        invalid_fields = set(values) - allowed_fields

        if invalid_fields:
            raise ValueError(
                "Unsupported game fields: "
                + ", ".join(sorted(invalid_fields))
            )

        game = await self.get_game(game_id)

        if game is None:
            return None

        if "pot" in values:
            pot = Decimal(
                str(values["pot"])
            )

            if pot < 0:
                raise ValueError(
                    "Game pot cannot be negative."
                )

            values["pot"] = pot

        if "game_data" in values:
            data = values["game_data"]

            if isinstance(data, dict):
                values["game_data"] = json.dumps(
                    data,
                    ensure_ascii=False,
                    default=str,
                )

        for field, value in values.items():
            setattr(game, field, value)

        await self.session.flush()

        return game

    async def start_game(
        self,
        game_id: int,
        *,
        started_at: datetime | None = None,
    ) -> Game | None:
        """
        Перевести игру в active.
        """

        game = await self.get_game(game_id)

        if game is None:
            return None

        game.status = "active"
        game.started_at = (
            started_at or datetime.now()
        )

        await self.session.flush()

        return game

    async def finish_game(
        self,
        game_id: int,
        *,
        winner_id: int | None = None,
        finished_at: datetime | None = None,
    ) -> Game | None:
        """
        Завершить игру.
        """

        game = await self.get_game(game_id)

        if game is None:
            return None

        game.status = "finished"
        game.winner_id = winner_id
        game.finished_at = (
            finished_at or datetime.now()
        )

        await self.session.flush()

        return game

    async def cancel_game(
        self,
        game_id: int,
    ) -> Game | None:
        """
        Отменить игру.
        """

        game = await self.get_game(game_id)

        if game is None:
            return None

        game.status = "cancelled"
        game.finished_at = datetime.now()

        await self.session.flush()

        return game

    # ========================================================================
    # GAME PLAYERS
    # ========================================================================

    async def get_player(
        self,
        *,
        game_id: int,
        user_id: int,
    ) -> GamePlayer | None:
        """
        Получить участника конкретной игры.
        """

        result = await self.session.execute(
            select(GamePlayer).where(
                GamePlayer.game_id == game_id,
                GamePlayer.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_player_by_id(
        self,
        player_id: int,
    ) -> GamePlayer | None:
        """
        Получить запись участника по ID.
        """

        result = await self.session.execute(
            select(GamePlayer).where(
                GamePlayer.id == player_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_game_players(
        self,
        game_id: int,
    ) -> Sequence[GamePlayer]:
        """
        Получить всех участников игры.
        """

        result = await self.session.execute(
            select(GamePlayer)
            .where(
                GamePlayer.game_id == game_id,
            )
            .order_by(
                GamePlayer.joined_at.asc(),
                GamePlayer.id.asc(),
            )
        )

        return result.scalars().all()

    async def count_game_players(
        self,
        game_id: int,
    ) -> int:
        """
        Количество участников игры.
        """

        players = await self.get_game_players(game_id)

        return len(players)

    async def add_player(
        self,
        *,
        game_id: int,
        user_id: int,
        bet: Decimal | int | float | str = Decimal("0.00"),
        player_data: dict[str, Any] | None = None,
    ) -> GamePlayer:
        """
        Добавить игрока в игровую сессию.
        """

        existing = await self.get_player(
            game_id=game_id,
            user_id=user_id,
        )

        if existing is not None:
            raise ValueError(
                "User is already participating in this game."
            )

        bet = Decimal(str(bet))

        if bet < 0:
            raise ValueError(
                "Player bet cannot be negative."
            )

        player_data_json: str | None = None

        if player_data is not None:
            player_data_json = json.dumps(
                player_data,
                ensure_ascii=False,
                default=str,
            )

        player = GamePlayer(
            game_id=game_id,
            user_id=user_id,
            bet=bet,
            player_data=player_data_json,
        )

        self.session.add(player)

        await self.session.flush()

        return player

    async def update_player(
        self,
        *,
        game_id: int,
        user_id: int,
        **values: object,
    ) -> GamePlayer | None:
        """
        Изменить состояние участника игры.
        """

        allowed_fields = {
            "bet",
            "payout",
            "result",
            "player_data",
        }

        invalid_fields = set(values) - allowed_fields

        if invalid_fields:
            raise ValueError(
                "Unsupported player fields: "
                + ", ".join(sorted(invalid_fields))
            )

        player = await self.get_player(
            game_id=game_id,
            user_id=user_id,
        )

        if player is None:
            return None

        if "bet" in values:
            bet = Decimal(
                str(values["bet"])
            )

            if bet < 0:
                raise ValueError(
                    "Player bet cannot be negative."
                )

            values["bet"] = bet

        if "payout" in values:
            payout = Decimal(
                str(values["payout"])
            )

            if payout < 0:
                raise ValueError(
                    "Player payout cannot be negative."
                )

            values["payout"] = payout

        if "player_data" in values:
            data = values["player_data"]

            if isinstance(data, dict):
                values["player_data"] = json.dumps(
                    data,
                    ensure_ascii=False,
                    default=str,
                )

        for field, value in values.items():
            setattr(player, field, value)

        await self.session.flush()

        return player

    async def set_player_result(
        self,
        *,
        game_id: int,
        user_id: int,
        result: str,
        payout: Decimal | int | float | str = Decimal("0.00"),
    ) -> GamePlayer | None:
        """
        Установить результат участника игры.
    
        Одновременно синхронизирует:
            GamePlayer.result
            GamePlayer.payout
            GameBet.payout
    
        Это важно для корректной истории ставок.
    
        result:
            winner
            loser
            draw
            bust
            cancelled
        """
    
        allowed_results = {
            "winner",
            "loser",
            "draw",
            "bust",
            "cancelled",
        }
    
        if result not in allowed_results:
            raise ValueError(
                f"Unsupported player result: {result}"
            )
    
        try:
            payout = Decimal(str(payout))
        except Exception as exc:
            raise ValueError(
                "Invalid player payout."
            ) from exc
    
        if not payout.is_finite():
            raise ValueError(
                "Player payout must be finite."
            )
    
        payout = payout.quantize(
            Decimal("0.01")
        )
    
        if payout < 0:
            raise ValueError(
                "Player payout cannot be negative."
            )
    
        player = await self.get_player(
            game_id=game_id,
            user_id=user_id,
        )
    
        if player is None:
            return None
    
        bet = await self.get_user_bet(
            game_id=game_id,
            user_id=user_id,
        )
    
        if bet is None:
            raise RuntimeError(
                "GamePlayer exists without corresponding GameBet."
            )
    
        player.result = result
        player.payout = payout
    
        bet.payout = payout
    
        await self.session.flush()
    
        return player
    
    
    # ========================================================================
    # GAME BETS
    # ========================================================================

    async def create_bet(
        self,
        *,
        game_id: int,
        user_id: int,
        amount: Decimal | int | float | str,
        bet_type: str,
        selection: str | None = None,
        payout: Decimal | int | float | str = Decimal("0.00"),
    ) -> GameBet:
        """
        Создать запись ставки.

        Финансовое списание выполняет EconomyService.
        Здесь только фиксируем факт ставки.
        """

        amount = Decimal(str(amount))
        payout = Decimal(str(payout))

        if amount <= 0:
            raise ValueError(
                "Bet amount must be greater than zero."
            )

        if payout < 0:
            raise ValueError(
                "Payout cannot be negative."
            )

        bet = GameBet(
            game_id=game_id,
            user_id=user_id,
            amount=amount,
            bet_type=bet_type,
            selection=selection,
            payout=payout,
        )

        self.session.add(bet)

        await self.session.flush()

        return bet

    async def get_bet(
        self,
        bet_id: int,
    ) -> GameBet | None:
        """
        Получить ставку по ID.
        """

        result = await self.session.execute(
            select(GameBet).where(
                GameBet.id == bet_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_game_bets(
        self,
        game_id: int,
    ) -> Sequence[GameBet]:
        """
        Получить все ставки игры.
        """

        result = await self.session.execute(
            select(GameBet)
            .where(
                GameBet.game_id == game_id,
            )
            .order_by(
                GameBet.created_at.asc(),
                GameBet.id.asc(),
            )
        )

        return result.scalars().all()

    async def get_user_bets(
        self,
        *,
        user_id: int,
        game_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[GameBet]:
        """
        История ставок пользователя.

        Если указан game_type, фильтрация происходит
        через связанную Game.
        """

        limit = max(1, min(limit, 1000))
        offset = max(0, offset)

        query = (
            select(GameBet)
            .join(
                Game,
                Game.id == GameBet.game_id,
            )
            .where(
                GameBet.user_id == user_id,
            )
        )

        if game_type is not None:
            query = query.where(
                Game.game_type == game_type,
            )

        query = (
            query
            .order_by(
                GameBet.created_at.desc(),
                GameBet.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    async def get_user_bet(
        self,
        *,
        game_id: int,
        user_id: int,
    ) -> GameBet | None:
        """
        Получить ставку пользователя в конкретной игре.
    
        Нужен для идемпотентности:
        повторная обработка одного Telegram update
        не должна создавать вторую GameBet.
        """
    
        result = await self.session.execute(
            select(GameBet)
            .where(
                GameBet.game_id == game_id,
                GameBet.user_id == user_id,
            )
            .order_by(
                GameBet.id.desc(),
            )
            .limit(1)
        )
    
        return result.scalar_one_or_none()

    async def update_bet_payout(
        self,
        bet_id: int,
        payout: Decimal | int | float | str,
    ) -> GameBet | None:
        """
        Обновить выплату по ставке.
        """

        payout = Decimal(str(payout))

        if payout < 0:
            raise ValueError(
                "Payout cannot be negative."
            )

        bet = await self.get_bet(bet_id)

        if bet is None:
            return None

        bet.payout = payout

        await self.session.flush()

        return bet