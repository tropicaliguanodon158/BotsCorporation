from __future__ import annotations

from aiogram import Dispatcher

# ============================================================================
# COMMON
# ============================================================================

from app.handlers.common.help import router as help_router
from app.handlers.common.profile import router as profile_router
from app.handlers.common.start import router as start_router

# ============================================================================
# CHARACTER
# ============================================================================

from app.handlers.character.abilities import router as abilities_router
from app.handlers.character.character import router as character_router
from app.handlers.character.inventory import (
    router as character_inventory_router,
)

# ============================================================================
# ECONOMY
# ============================================================================

from app.handlers.economy.balance import router as balance_router
from app.handlers.economy.bank import router as bank_router
from app.handlers.economy.rewards import router as rewards_router
from app.handlers.economy.shop import router as shop_router

# ============================================================================
# FOUNDER PANEL
# ============================================================================

from app.handlers.founder.abilities import router as founder_abilities_router
from app.handlers.founder.cases import router as founder_cases_router
from app.handlers.founder.chats import router as founder_chats_router
from app.handlers.founder.economy import router as founder_economy_router
from app.handlers.founder.moderation import (
    router as founder_moderation_router,
)
from app.handlers.founder.panel import router as founder_panel_router
from app.handlers.founder.races import router as founder_races_router
from app.handlers.founder.ranks import router as founder_ranks_router
from app.handlers.founder.shop import router as founder_shop_router
from app.handlers.founder.users import router as founder_users_router

# ============================================================================
# GAMES
# ============================================================================

from app.handlers.games.blackjack import router as blackjack_router
from app.handlers.games.dice import router as dice_router
from app.handlers.games.duel import router as duel_router
from app.handlers.games.roulette import router as roulette_router

# ============================================================================
# INTERACTIONS
# ============================================================================

from app.handlers.interactions.interactions import (
    router as interactions_router,
)

# ============================================================================
# MODERATION
# ============================================================================

from app.handlers.moderation.filters import (
    router as moderation_filters_router,
)
from app.handlers.moderation.moderation import (
    router as moderation_router,
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

from app.middlewares.antiflood import AntiFloodMiddleware
from app.middlewares.database import DatabaseMiddleware
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.user import UserMiddleware


def create_dispatcher() -> Dispatcher:
    """
    Создать и полностью настроить Dispatcher.

    Порядок:

        Telegram update
            ↓
        LoggingMiddleware
            ↓
        DatabaseMiddleware
            ↓
        UserMiddleware
            ↓
        Router
            ↓
        Handler
            ↓
        commit / rollback
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

    dp.message.outer_middleware(
        AntiFloodMiddleware(),
    )

    # ========================================================================
    # COMMON
    # ========================================================================

    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(profile_router)

    # ========================================================================
    # CHARACTER
    # ========================================================================

    dp.include_router(character_router)
    dp.include_router(character_inventory_router)
    dp.include_router(abilities_router)

    # ========================================================================
    # ECONOMY
    # ========================================================================

    dp.include_router(balance_router)
    dp.include_router(bank_router)
    dp.include_router(rewards_router)
    dp.include_router(shop_router)

    # ========================================================================
    # GAMES
    # ========================================================================

    dp.include_router(dice_router)
    dp.include_router(roulette_router)
    dp.include_router(duel_router)
    dp.include_router(blackjack_router)

    # ========================================================================
    # INTERACTIONS
    # ========================================================================

    dp.include_router(interactions_router)

    # ========================================================================
    # MODERATION
    # ========================================================================

    dp.include_router(moderation_router)
    dp.include_router(moderation_filters_router)

    # ========================================================================
    # FOUNDER PANEL
    # ========================================================================

    dp.include_router(founder_panel_router)
    dp.include_router(founder_users_router)
    dp.include_router(founder_economy_router)
    dp.include_router(founder_cases_router)
    dp.include_router(founder_abilities_router)
    dp.include_router(founder_races_router)
    dp.include_router(founder_ranks_router)
    dp.include_router(founder_shop_router)
    dp.include_router(founder_chats_router)
    dp.include_router(founder_moderation_router)

    return dp