"""
Rewards service.

Бизнес-логика наград.

Repository:
    - EconomyRepository -> деньги / гемы / транзакции
    - SettingsRepository -> настройки чата

Service:
    - определяет размер награды;
    - применяет множители;
    - выдаёт валюту;
    - выдаёт XP / gems;
    - проверяет настройки;
    - не выполняет commit().

Важно:
    Service НЕ работает напрямую с Telegram API.
    Service НЕ содержит SQL-запросов.
    Service НЕ управляет транзакцией самостоятельно.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.repositories.economy import EconomyRepository
from app.repositories.settings import SettingsRepository


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

    Отвечает только за бизнес-логику наград.

    Основные сценарии:

        message_reward()
        photo_reward()
        video_reward()
        hourly_reward()
        daily_reward()
        custom_reward()

    Все настройки берутся через SettingsRepository.

    Финансовые изменения выполняются через EconomyRepository.
    """

    # ------------------------------------------------------------------------
    # DEFAULT SETTINGS
    # ------------------------------------------------------------------------

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

    # ------------------------------------------------------------------------
    # SETTINGS KEYS
    # ------------------------------------------------------------------------

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

    # ------------------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------------------

    def __init__(
        self,
        *,
        economy_repository: EconomyRepository,
        settings_repository: SettingsRepository,
    ) -> None:
        self.economy = economy_repository
        self.settings = settings_repository

    # ========================================================================
    # INTERNAL
    # ========================================================================

    async def _get_setting(
        self,
        *,
        chat_id: int | None,
        key: str,
        default: Any,
    ) -> Any:
        """
        Получить настройку чата.

        Если chat_id отсутствует, используется default.
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
        except Exception:
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
        except (TypeError, ValueError):
            return default

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

        Награда определяется настройками конкретного чата.
        """

        message_type = message_type.lower().strip()

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
            currency=self._decimal(currency),
            xp=self._int(xp),
            gems=self._int(gems),
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
        Награда за фотографию.
        """

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
            currency=self._decimal(currency),
            xp=self._int(xp),
            gems=self._int(gems),
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
        Награда за видео.
        """

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
            currency=self._decimal(currency),
            xp=self._int(xp),
            gems=self._int(gems),
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

        ВАЖНО:

        Сам факт того, что пользователь уже получал
        hourly reward, здесь НЕ проверяется.

        Это намеренно.

        Проверка cooldown / последнего получения должна
        выполняться через слой активности/награду,
        когда соответствующий repository будет подключён.
        """

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
            currency=self._decimal(currency),
            xp=self._int(xp),
            gems=self._int(gems),
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

        Проверка того, получал ли пользователь награду
        сегодня, намеренно находится вне этого метода.

        Этот сервис отвечает за СУММУ награды,
        а не за хранение состояния активности.
        """

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
            currency=self._decimal(currency),
            xp=self._int(xp),
            gems=self._int(gems),
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
            - специальных механик.
        """

        currency = self._decimal(currency)

        xp = self._int(xp)
        gems = self._int(gems)

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
            source=source,
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

        Деньги и гемы проходят через EconomyRepository.

        XP пока не изменяется здесь, потому что UserRepository
        в текущей утверждённой архитектуре этим сервисом
        в данном файле не подключён.

        Поэтому XP возвращается как часть результата,
        а фактическое изменение User.xp должно выполняться
        существующим user/progression service.

        Это специально сделано так, чтобы RewardsService
        не начал напрямую лазить в SQLAlchemy-модели.
        """

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
        # RESULT
        # ------------------------------------------------------------------

        return RewardResult(
            user_id=user_id,
            chat_id=chat_id,
            currency=currency,
            gems=gems,
            xp=xp,
            source=source,
            rewarded=True,
        )