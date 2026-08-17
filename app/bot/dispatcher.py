from __future__ import annotations

from aiogram import Dispatcher

from app.handlers.common.help import router as help_router
from app.handlers.common.profile import router as profile_router
from app.handlers.common.start import router as start_router

from app.handlers.economy.balance import router as balance_router
from app.handlers.economy.bank import router as bank_router
from app.handlers.economy.rewards import router as rewards_router
from app.handlers.economy.shop import router as shop_router

from app.handlers.games.dice import router as dice_router
from app.handlers.games.duel import router as duel_router
from app.handlers.games.roulette import router as roulette_router

from app.middlewares.database import DatabaseMiddleware
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.user import UserMiddleware


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    # ========================================================================
    # MIDDLEWARE
    # ========================================================================

    dp.update.outer_middleware(
        LoggingMiddleware(),
    )

    dp.update.outer_middleware(
        DatabaseMiddleware(),
    )

    dp.update.outer_middleware(
        UserMiddleware(),
    )

    # ========================================================================
    # COMMON
    # ========================================================================

    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(profile_router)

    # ========================================================================
    # ECONOMY
    # ========================================================================

    dp.include_router(balance_router)
    dp.include_router(rewards_router)
    dp.include_router(bank_router)
    dp.include_router(shop_router)

    # ========================================================================
    # GAMES
    # ========================================================================

    dp.include_router(dice_router)
    dp.include_router(roulette_router)
    dp.include_router(duel_router)

    return dp