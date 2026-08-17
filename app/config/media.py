"""
Все Telegram file_id / URL картинок проекта.

Сюда НЕ надо загружать сами изображения.

Для Telegram лучше использовать file_id.

Как получить:
1. Отправь картинку боту.
2. Временно выведи message.photo[-1].file_id.
3. Скопируй file_id сюда.
"""


# ============================================================================
# COMMAND IMAGES
# ============================================================================

COMMAND_IMAGES: dict[str, str | None] = {
    "start": None,
    "help": None,
    "profile": None,
    "balance": None,
    "shop": None,
    "daily": None,
    "hourly": None,
    "character": None,
    "inventory": None,
    "abilities": None,
    "cases": None,
    "level_up": None,
    "rank_up": None,
}


# ============================================================================
# INTERACTION IMAGE POOLS
# ============================================================================

INTERACTION_IMAGES: dict[str, list[str]] = {
    "hit": [
        # "AgACAgIAAxkBA...",
        # "AgACAgIAAxkBA...",
        # "AgACAgIAAxkBA...",
    ],

    "kiss": [
        # "AgACAgIAAxkBA...",
    ],

    "hug": [
        # "AgACAgIAAxkBA...",
    ],

    "slap": [
        # "AgACAgIAAxkBA...",
    ],

    "kick": [
        # "AgACAgIAAxkBA...",
    ],

    "bite": [
        # "AgACAgIAAxkBA...",
    ],

    "piss": [
        # "AgACAgIAAxkBA...",
    ],
}