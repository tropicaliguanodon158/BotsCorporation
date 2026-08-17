"""
Rewards service.

Бизнес-логика системы наград.

Отвечает за:
    - награду за сообщение;
    - награду за фото;
    - награду за видео;
    - часовую награду;
    - ежедневную награду;
    - произвольные награды;
    - начисление валюты;
    - начисление гемов;
    - начисление XP.

Repository:
    - EconomyRepository -> деньги / гемы / транзакции;
    - SettingsRepository -> настройки чата;
    - UserRepository -> XP и данные пользователя.

Service:
    - определяет размер награды;
    - получает настройки;
    - применяет бизнес-правила;
    - вызывает repositories;
    - не содержит SQL;
    - не работает напрямую с Telegram API;
    - не выполняет commit() / rollback().

Транзакция управляется уровнем middleware/application.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.database.repositories.economy import EconomyRepository
from app.database.repositories.settings import SettingsRepository
from app.database.repositories.users import UserRepository


# ============================================================================
# RESULT
# ============================================================================


@dataclass(slots=True)
class RewardResult:
    """
    Результат выдачи награды.
    """

    user_id: int

    chat_id: int | None

    currency: Decimal = Decimal("0.00")

    gems: int = 0

    xp: int = 0

    source: str = ""

    rewarded: bool = False

    reason: str | None = None


# ============================================================================
# SERVICE
# ============================================================================


class RewardsService:
    """
    Сервис системы наград.

    Основные сценарии:

        message_reward()
        photo_reward()
        video_reward()
        hourly_reward()
        daily_reward()
        custom_reward()

    Сервис не знает о Telegram API.

    Он получает уже подготовленные данные от handler/service
    и изменяет состояние через repositories.
    """

    # ========================================================================
    # DEFAULT SETTINGS
    # ========================================================================

    DEFAULT_MESSAGE_REWARD = Decimal("1.00")
    DEFAULT_PHOTO_REWARD = Decimal("3.00")
    DEFAULT_VIDEO_REWARD = Decimal("5.00")

    DEFAULT_MESSAGE_XP = 1
    DEFAULT_PHOTO_XP = 2
    DEFAULT_VIDEO_XP = 3

    DEFAULT_MESSAGE_GEMS = 0
    DEFAULT_PHOTO_GEMS = 0
    DEFAULT_VIDEO_GEMS = 0

    DEFAULT_HOURLY_REWARD = Decimal("25.00")
    DEFAULT_HOURLY_XP = 10
    DEFAULT_HOURLY_GEMS = 0

    DEFAULT_DAILY_REWARD = Decimal("100.00")
    DEFAULT_DAILY_XP = 50
    DEFAULT_DAILY_GEMS = 1

    # ========================================================================
    # SETTINGS KEYS
    # ========================================================================

    SETTING_MESSAGE_REWARD = "rewards.message.currency"
    SETTING_MESSAGE_XP = "rewards.message.xp"
    SETTING_MESSAGE_GEMS = "rewards.message.gems"

    SETTING_PHOTO_REWARD = "rewards.photo.currency"
    SETTING_PHOTO_XP = "rewards.photo.xp"
    SETTING_PHOTO_GEMS = "rewards.photo.gems"

    SETTING_VIDEO_REWARD = "rewards.video.currency"
    SETTING_VIDEO_XP = "rewards.video.xp"
    SETTING_VIDEO_GEMS = "rewards.video.gems"

    SETTING_HOURLY_REWARD = "rewards.hourly.currency"
    SETTING_HOURLY_XP = "rewards.hourly.xp"
    SETTING_HOURLY_GEMS = "rewards.hourly.gems"

    SETTING_DAILY_REWARD = "rewards.daily.currency"
    SETTING_DAILY_XP = "rewards.daily.xp"
    SETTING_DAILY_GEMS = "rewards.daily.gems"

    # ========================================================================
    # INIT
    # ========================================================================

    def __init__(
        self,
        *,
        economy_repository: EconomyRepository,
        settings_repository: SettingsRepository,
        user_repository: UserRepository,
    ) -> None:
        self.economy = economy_repository
        self.settings = settings_repository
        self.users = user_repository

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    async def _get_setting(
        self,
        *,
        chat_id: int | None,
        key: str,
        default: Any,
    ) -> Any:
        """
        Получить настройку конкретного чата.

        Если chat_id отсутствует или чат ещё не зарегистрирован,
        возвращается default.
        """

        if chat_id is None:
            return default

        return await self.settings.get(
            chat_id=chat_id,
            key=key,
            default=default,
        )

    @staticmethod
    def _decimal(
        value: Any,
        default: Decimal = Decimal("0.00"),
    ) -> Decimal:
        """
        Безопасно преобразовать значение в Decimal.
        """

        if value is None:
            return default

        try:
            result = Decimal(str(value))
        except (
            TypeError,
            ValueError,
        ):
            return default

        if not result.is_finite():
            return default

        return result.quantize(
            Decimal("0.01")
        )

    @staticmethod
    def _int(
        value: Any,
        default: int = 0,
    ) -> int:
        """
        Безопасно преобразовать значение в int.
        """

        if value is None:
            return default

        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _validate_user_id(
        user_id: int,
    ) -> None:
        """
        Проверить Telegram user ID.
        """

        if user_id <= 0:
            raise ValueError(
                "Invalid user_id."
            )

    # ========================================================================
    # MESSAGE
    # ========================================================================

    async def message_reward(
        self,
        *,
        user_id: int,
        chat_id: int | None,
        message_type: str = "text",
    ) -> RewardResult:
        """
        Выдать награду за сообщение.

        message_type:

            text
            photo
            video
            other
        """

        self._validate_user_id(user_id)

        message_type = (
            message_type
            .lower()
            .strip()
        )

        if message_type == "photo":
            return await self.photo_reward(
                user_id=user_id,
                chat_id=chat_id,
            )

        if message_type == "video":
            return await self.video_reward(
                user_id=user_id,
                chat_id=chat_id,
            )

        if message_type not in {
            "text",
            "other",
        }:
            message_type = "text"

        currency = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_MESSAGE_REWARD,
            default=self.DEFAULT_MESSAGE_REWARD,
        )

        xp = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_MESSAGE_XP,
            default=self.DEFAULT_MESSAGE_XP,
        )

        gems = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_MESSAGE_GEMS,
            default=self.DEFAULT_MESSAGE_GEMS,
        )

        return await self._grant_reward(
            user_id=user_id,
            chat_id=chat_id,
            currency=self._decimal(
                currency,
                self.DEFAULT_MESSAGE_REWARD,
            ),
            xp=self._int(
                xp,
                self.DEFAULT_MESSAGE_XP,
            ),
            gems=self._int(
                gems,
                self.DEFAULT_MESSAGE_GEMS,
            ),
            source="message",
        )

    # ========================================================================
    # PHOTO
    # ========================================================================

    async def photo_reward(
        self,
        *,
        user_id: int,
        chat_id: int | None,
    ) -> RewardResult:
        """
        Выдать награду за фотографию.
        """

        self._validate_user_id(user_id)

        currency = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_PHOTO_REWARD,
            default=self.DEFAULT_PHOTO_REWARD,
        )

        xp = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_PHOTO_XP,
            default=self.DEFAULT_PHOTO_XP,
        )

        gems = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_PHOTO_GEMS,
            default=self.DEFAULT_PHOTO_GEMS,
        )

        return await self._grant_reward(
            user_id=user_id,
            chat_id=chat_id,
            currency=self._decimal(
                currency,
                self.DEFAULT_PHOTO_REWARD,
            ),
            xp=self._int(
                xp,
                self.DEFAULT_PHOTO_XP,
            ),
            gems=self._int(
                gems,
                self.DEFAULT_PHOTO_GEMS,
            ),
            source="photo",
        )

    # ========================================================================
    # VIDEO
    # ========================================================================

    async def video_reward(
        self,
        *,
        user_id: int,
        chat_id: int | None,
    ) -> RewardResult:
        """
        Выдать награду за видео.
        """

        self._validate_user_id(user_id)

        currency = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_VIDEO_REWARD,
            default=self.DEFAULT_VIDEO_REWARD,
        )

        xp = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_VIDEO_XP,
            default=self.DEFAULT_VIDEO_XP,
        )

        gems = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_VIDEO_GEMS,
            default=self.DEFAULT_VIDEO_GEMS,
        )

        return await self._grant_reward(
            user_id=user_id,
            chat_id=chat_id,
            currency=self._decimal(
                currency,
                self.DEFAULT_VIDEO_REWARD,
            ),
            xp=self._int(
                xp,
                self.DEFAULT_VIDEO_XP,
            ),
            gems=self._int(
                gems,
                self.DEFAULT_VIDEO_GEMS,
            ),
            source="video",
        )

    # ========================================================================
    # HOURLY
    # ========================================================================

    async def hourly_reward(
        self,
        *,
        user_id: int,
        chat_id: int | None,
    ) -> RewardResult:
        """
        Выдать часовую награду.

        Проверка cooldown здесь НЕ выполняется.

        Этот метод отвечает за размер и фактическую выдачу
        награды.

        Проверка возможности получения hourly reward
        будет находиться в соответствующем service/handler
        после подключения activity/cooldown механики.
        """

        self._validate_user_id(user_id)

        currency = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_HOURLY_REWARD,
            default=self.DEFAULT_HOURLY_REWARD,
        )

        xp = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_HOURLY_XP,
            default=self.DEFAULT_HOURLY_XP,
        )

        gems = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_HOURLY_GEMS,
            default=self.DEFAULT_HOURLY_GEMS,
        )

        return await self._grant_reward(
            user_id=user_id,
            chat_id=chat_id,
            currency=self._decimal(
                currency,
                self.DEFAULT_HOURLY_REWARD,
            ),
            xp=self._int(
                xp,
                self.DEFAULT_HOURLY_XP,
            ),
            gems=self._int(
                gems,
                self.DEFAULT_HOURLY_GEMS,
            ),
            source="hourly_reward",
        )

    # ========================================================================
    # DAILY
    # ========================================================================

    async def daily_reward(
        self,
        *,
        user_id: int,
        chat_id: int | None,
    ) -> RewardResult:
        """
        Выдать ежедневную награду.

        Проверка "получал ли пользователь сегодня"
        находится за пределами этого метода.
        """

        self._validate_user_id(user_id)

        currency = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_DAILY_REWARD,
            default=self.DEFAULT_DAILY_REWARD,
        )

        xp = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_DAILY_XP,
            default=self.DEFAULT_DAILY_XP,
        )

        gems = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_DAILY_GEMS,
            default=self.DEFAULT_DAILY_GEMS,
        )

        return await self._grant_reward(
            user_id=user_id,
            chat_id=chat_id,
            currency=self._decimal(
                currency,
                self.DEFAULT_DAILY_REWARD,
            ),
            xp=self._int(
                xp,
                self.DEFAULT_DAILY_XP,
            ),
            gems=self._int(
                gems,
                self.DEFAULT_DAILY_GEMS,
            ),
            source="daily_reward",
        )

    # ========================================================================
    # CUSTOM
    # ========================================================================

    async def custom_reward(
        self,
        *,
        user_id: int,
        chat_id: int | None,
        currency: Decimal | int | float | str = Decimal("0.00"),
        xp: int = 0,
        gems: int = 0,
        source: str = "custom_reward",
    ) -> RewardResult:
        """
        Универсальная выдача награды.

        Используется для:

            - заданий;
            - достижений;
            - событий;
            - административных наград;
            - игровых механик;
            - специальных событий.
        """

        self._validate_user_id(user_id)

        if not source or not source.strip():
            raise ValueError(
                "Reward source cannot be empty."
            )

        currency = self._decimal(currency)

        xp = self._int(xp)

        gems = self._int(gems)

        if currency < 0:
            raise ValueError(
                "Currency reward cannot be negative."
            )

        if xp < 0:
            raise ValueError(
                "XP reward cannot be negative."
            )

        if gems < 0:
            raise ValueError(
                "Gem reward cannot be negative."
            )

        return await self._grant_reward(
            user_id=user_id,
            chat_id=chat_id,
            currency=currency,
            xp=xp,
            gems=gems,
            source=source.strip(),
        )

    # ========================================================================
    # INTERNAL GRANT
    # ========================================================================

    async def _grant_reward(
        self,
        *,
        user_id: int,
        chat_id: int | None,
        currency: Decimal,
        xp: int,
        gems: int,
        source: str,
    ) -> RewardResult:
        """
        Фактически выдать награду.

        Все изменения выполняются через repositories.

        Никакого SQLAlchemy здесь нет.
        """

        self._validate_user_id(user_id)

        if currency < 0:
            raise ValueError(
                "Currency reward cannot be negative."
            )

        if xp < 0:
            raise ValueError(
                "XP reward cannot be negative."
            )

        if gems < 0:
            raise ValueError(
                "Gem reward cannot be negative."
            )

        if not source or not source.strip():
            raise ValueError(
                "Reward source cannot be empty."
            )

        source = source.strip()

        # ------------------------------------------------------------------
        # CURRENCY
        # ------------------------------------------------------------------

        if currency > 0:
            await self.economy.add_balance(
                user_id=user_id,
                amount=currency,
                transaction_type="reward",
                source=source,
                reference_id=None,
            )

        # ------------------------------------------------------------------
        # GEMS
        # ------------------------------------------------------------------

        if gems > 0:
            await self.economy.add_gems(
                user_id=user_id,
                amount=gems,
            )

        # ------------------------------------------------------------------
        # XP
        # ------------------------------------------------------------------

        if xp > 0:
            user = await self.users.add_xp(
                user_id=user_id,
                amount=xp,
            )

            if user is None:
                raise ValueError(
                    f"User {user_id} does not exist."
                )

        # ------------------------------------------------------------------
        # RESULT
        # ------------------------------------------------------------------

        rewarded = (
            currency > 0
            or gems > 0
            or xp > 0
        )

        return RewardResult(
            user_id=user_id,
            chat_id=chat_id,
            currency=currency,
            gems=gems,
            xp=xp,
            source=source,
            rewarded=rewarded,
            reason=None if rewarded else "empty_reward",
        )