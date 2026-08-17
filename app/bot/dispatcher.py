from __future__ import annotations

from aiogram import Dispatcher

from app.handlers.common.help import router as help_router
from app.handlers.common.profile import router as profile_router
from app.handlers.common.start import router as start_router
from app.handlers.economy.balance import router as balance_router
from app.handlers.economy.rewards import router as rewards_router

from app.middlewares.database import DatabaseMiddleware
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.user import UserMiddleware


def create_dispatcher() -> Dispatcher:
    """
    Создаёт главный Dispatcher приложения.

    Здесь собираются:

        - middleware;
        - пользовательские роутеры;
        - Telegram handlers.

    Бизнес-логика здесь отсутствует.
    """

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
    # ROUTERS
    # ========================================================================

    dp.include_router(
        start_router,
    )

    dp.include_router(
        help_router,
    )

    dp.include_router(
        profile_router,
    )

    dp.include_router(
        balance_router,
    )

    dp.include_router(
        rewards_router,
    )

    return dp