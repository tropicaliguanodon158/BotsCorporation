"""
Database models.

Центральная точка импорта всех SQLAlchemy-моделей проекта.

Все модели должны быть импортированы здесь до создания
metadata / запуска миграций, чтобы SQLAlchemy видел все таблицы.
"""

from app.database.models.base import Base


# ============================================================================
# USER
# ============================================================================

from app.database.models.user import User


# ============================================================================
# CHAT
# ============================================================================

from app.database.models.chat import Chat


# ============================================================================
# ECONOMY
# ============================================================================

from app.database.models.economy import (
    Wallet,
    Transaction,
)


# ============================================================================
# CHARACTER
# ============================================================================

from app.database.models.character import (
    Race,
    CharacterRank,
    Ability,
    Character,
    CharacterAbility,
)


# ============================================================================
# INVENTORY
# ============================================================================

from app.database.models.inventory import (
    Item,
    InventoryItem,
    Equipment,
)


# ============================================================================
# MODERATION
# ============================================================================

from app.database.models.moderation import (
    ModerationAction,
    UserWarning,
    ModerationFilter,
)


# ============================================================================
# GAMES
# ============================================================================

from app.database.models.games import (
    Game,
    GamePlayer,
    GameBet,
)


# ============================================================================
# ADMINISTRATION
# ============================================================================

from app.database.models.admin import (
    AdminLevel,
    Permission,
    AdminLevelPermission,
    ChatAdmin,
    AdminActionLog,
)


# ============================================================================
# CASES
# ============================================================================

from app.database.models.cases import (
    Case,
    CaseReward,
    CaseOpening,
)


# ============================================================================
# TASKS / ACHIEVEMENTS / ACTIVITY
# ============================================================================

from app.database.models.tasks import (
    UserDailyActivity,
    Task,
    UserTask,
    Achievement,
    UserAchievement,
)


# ============================================================================
# PASSIVE INCOME
# ============================================================================

from app.database.models.passive_income import (
    PassiveIncomeType,
    UserPassiveIncome,
    PassiveIncomePayout,
)


# ============================================================================
# INTERACTIONS
# ============================================================================

from app.database.models.interactions import (
    InteractionType,
    UserInteractionCooldown,
    InteractionLog,
)


# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    # Base
    "Base",

    # User
    "User",

    # Chat
    "Chat",

    # Economy
    "Wallet",
    "Transaction",

    # Character
    "Race",
    "CharacterRank",
    "Ability",
    "Character",
    "CharacterAbility",

    # Inventory
    "Item",
    "InventoryItem",
    "Equipment",

    # Moderation
    "ModerationAction",
    "UserWarning",
    "ModerationFilter",

    # Games
    "Game",
    "GamePlayer",
    "GameBet",

    # Administration
    "AdminLevel",
    "Permission",
    "AdminLevelPermission",
    "ChatAdmin",
    "AdminActionLog",

    # Cases
    "Case",
    "CaseReward",
    "CaseOpening",

    # Tasks
    "UserDailyActivity",
    "Task",
    "UserTask",

    # Achievements
    "Achievement",
    "UserAchievement",

    # Passive income
    "PassiveIncomeType",
    "UserPassiveIncome",
    "PassiveIncomePayout",

    # Interactions
    "InteractionType",
    "UserInteractionCooldown",
    "InteractionLog",
]