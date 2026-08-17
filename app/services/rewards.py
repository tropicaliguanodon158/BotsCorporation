from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from app.services.progression import ProgressionService

from app.database.repositories.economy import EconomyRepository
from app.database.repositories.settings import SettingsRepository
from app.database.repositories.users import UserRepository


@dataclass(slots=True)
class RewardResult:
    user_id: int
    chat_id: int | None
    currency: Decimal = Decimal("0.00")
    gems: int = 0
    xp: int = 0
    source: str = ""
    rewarded: bool = False
    reason: str | None = None


class RewardsService:
    """
    Единый сервис наград.

    Все изменения выполняются внутри внешней DB-транзакции.

    Для конкурентных операций пользователь блокируется через
    SELECT ... FOR UPDATE.

    Это особенно важно для:
        - награды за сообщения;
        - hourly;
        - daily;
        - анти-спам cooldown.
    """

    DEFAULT_MESSAGE_REWARD = Decimal("1.00")
    DEFAULT_PHOTO_REWARD = Decimal("3.00")
    DEFAULT_VIDEO_REWARD = Decimal("5.00")

    DEFAULT_MESSAGE_XP = 1
    DEFAULT_PHOTO_XP = 2
    DEFAULT_VIDEO_XP = 3

    DEFAULT_MESSAGE_GEMS = 0
    DEFAULT_PHOTO_GEMS = 0
    DEFAULT_VIDEO_GEMS = 0

    DEFAULT_MESSAGE_COOLDOWN = 10

    DEFAULT_HOURLY_REWARD = Decimal("25.00")
    DEFAULT_HOURLY_XP = 10
    DEFAULT_HOURLY_GEMS = 0

    DEFAULT_DAILY_REWARD = Decimal("100.00")
    DEFAULT_DAILY_XP = 50
    DEFAULT_DAILY_GEMS = 1

    SETTING_MESSAGE_REWARD = "rewards.message.currency"
    SETTING_MESSAGE_XP = "rewards.message.xp"
    SETTING_MESSAGE_GEMS = "rewards.message.gems"
    SETTING_MESSAGE_COOLDOWN = "rewards.message.cooldown"

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
    # HELPERS
    # ========================================================================

    @staticmethod
    def _validate_user_id(user_id: int) -> None:
        if user_id <= 0:
            raise ValueError("Invalid user_id.")

    @staticmethod
    def _now() -> datetime:
        return datetime.now()

    @staticmethod
    def _decimal(
        value: Any,
        default: Decimal = Decimal("0.00"),
    ) -> Decimal:
        if value is None:
            return default

        try:
            result = Decimal(str(value))
        except (TypeError, ValueError):
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
        if value is None:
            return default

        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    async def _get_setting(
        self,
        *,
        chat_id: int | None,
        key: str,
        default: Any,
    ) -> Any:
        if chat_id is None:
            return default

        return await self.settings.get(
            chat_id=chat_id,
            key=key,
            default=default,
        )

    async def _has_recent_transaction(
        self,
        *,
        user_id: int,
        source: str,
        since: datetime,
    ) -> bool:
        """
        Проверяет наличие недавней транзакции
        указанного типа.

        Запрос выполняется непосредственно к БД,
        без загрузки истории транзакций пользователя.
        """

        return await self.economy.has_recent_transaction(
            user_id=user_id,
            source=source,
            since=since,
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
        self._validate_user_id(user_id)

        message_type = message_type.strip().lower()

        cooldown = await self._get_setting(
            chat_id=chat_id,
            key=self.SETTING_MESSAGE_COOLDOWN,
            default=self.DEFAULT_MESSAGE_COOLDOWN,
        )

        cooldown = max(
            0,
            self._int(
                cooldown,
                self.DEFAULT_MESSAGE_COOLDOWN,
            ),
        )

        # Все типы сообщений используют общий cooldown.
        # Это предотвращает фарм через чередование
        # text -> photo -> video.
        source_map = {
            "text": (
                self.SETTING_MESSAGE_REWARD,
                self.SETTING_MESSAGE_XP,
                self.SETTING_MESSAGE_GEMS,
                self.DEFAULT_MESSAGE_REWARD,
                self.DEFAULT_MESSAGE_XP,
                self.DEFAULT_MESSAGE_GEMS,
                "message",
            ),
            "other": (
                self.SETTING_MESSAGE_REWARD,
                self.SETTING_MESSAGE_XP,
                self.SETTING_MESSAGE_GEMS,
                self.DEFAULT_MESSAGE_REWARD,
                self.DEFAULT_MESSAGE_XP,
                self.DEFAULT_MESSAGE_GEMS,
                "message",
            ),
            "photo": (
                self.SETTING_PHOTO_REWARD,
                self.SETTING_PHOTO_XP,
                self.SETTING_PHOTO_GEMS,
                self.DEFAULT_PHOTO_REWARD,
                self.DEFAULT_PHOTO_XP,
                self.DEFAULT_PHOTO_GEMS,
                "photo",
            ),
            "video": (
                self.SETTING_VIDEO_REWARD,
                self.SETTING_VIDEO_XP,
                self.SETTING_VIDEO_GEMS,
                self.DEFAULT_VIDEO_REWARD,
                self.DEFAULT_VIDEO_XP,
                self.DEFAULT_VIDEO_GEMS,
                "video",
            ),
        }

        if message_type not in source_map:
            message_type = "text"

        (
            currency_key,
            xp_key,
            gems_key,
            currency_default,
            xp_default,
            gems_default,
            source,
        ) = source_map[message_type]

        # --------------------------------------------------------------------
        # Критическая секция.
        #
        # Блокируем строку пользователя ДО проверки cooldown.
        # Поэтому два одновременных update одного пользователя
        # не смогут одновременно пройти проверку.
        # --------------------------------------------------------------------

        user = await self.users.get_by_id_for_update(
            user_id
        )

        if user is None:
            raise ValueError(
                f"User {user_id} does not exist."
            )

        if cooldown > 0:
            since = self._now() - timedelta(
                seconds=cooldown
            )

            if await self._has_recent_transaction(
                user_id=user_id,
                source="message",
                since=since,
            ) or await self._has_recent_transaction(
                user_id=user_id,
                source="photo",
                since=since,
            ) or await self._has_recent_transaction(
                user_id=user_id,
                source="video",
                since=since,
            ):
                return RewardResult(
                    user_id=user_id,
                    chat_id=chat_id,
                    source=source,
                    rewarded=False,
                    reason="cooldown",
                )

        currency = await self._get_setting(
            chat_id=chat_id,
            key=currency_key,
            default=currency_default,
        )

        xp = await self._get_setting(
            chat_id=chat_id,
            key=xp_key,
            default=xp_default,
        )

        gems = await self._get_setting(
            chat_id=chat_id,
            key=gems_key,
            default=gems_default,
        )

        return await self._grant_reward(
            user_id=user_id,
            chat_id=chat_id,
            currency=self._decimal(
                currency,
                currency_default,
            ),
            xp=self._int(
                xp,
                xp_default,
            ),
            gems=self._int(
                gems,
                gems_default,
            ),
            source=source,
        )

    # ========================================================================
    # HOURLY
    # ========================================================================

    async def hourly_reward(
        self,
        *,
        user_id: int,
        chat_id: int | None = None,
    ) -> RewardResult:
        self._validate_user_id(user_id)

        user = await self.users.get_by_id_for_update(
            user_id
        )

        if user is None:
            raise ValueError(
                f"User {user_id} does not exist."
            )

        now = self._now()

        # ------------------------------------------------------------
        # Hourly cooldown
        #
        # Храним время последнего получения непосредственно
        # в users.last_hourly_at.
        #
        # Это не зависит от transactions и не позволяет
        # повторно забрать hourly после успешной выдачи.
        # ------------------------------------------------------------

        if user.last_hourly_at is not None:
            elapsed = now - user.last_hourly_at

            if elapsed < timedelta(hours=1):
                return RewardResult(
                    user_id=user_id,
                    chat_id=chat_id,
                    source="hourly_reward",
                    rewarded=False,
                    reason="cooldown",
                )

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

        currency = self._decimal(
            currency,
            self.DEFAULT_HOURLY_REWARD,
        )

        xp = self._int(
            xp,
            self.DEFAULT_HOURLY_XP,
        )

        gems = self._int(
            gems,
            self.DEFAULT_HOURLY_GEMS,
        )

        result = await self._grant_reward(
            user_id=user_id,
            chat_id=chat_id,
            currency=currency,
            xp=xp,
            gems=gems,
            source="hourly_reward",
        )

        if result.rewarded:
            user.last_hourly_at = now

        return result

    # ========================================================================
    # DAILY
    # ========================================================================

    async def daily_reward(
        self,
        *,
        user_id: int,
        chat_id: int | None,
    ) -> RewardResult:
        self._validate_user_id(user_id)

        user = await self.users.get_by_id_for_update(
            user_id
        )

        if user is None:
            raise ValueError(
                f"User {user_id} does not exist."
            )

        now = self._now()

        start_of_day = datetime(
            now.year,
            now.month,
            now.day,
        )

        if await self._has_recent_transaction(
            user_id=user_id,
            source="daily_reward",
            since=start_of_day,
        ):
            return RewardResult(
                user_id=user_id,
                chat_id=chat_id,
                source="daily_reward",
                rewarded=False,
                reason="already_claimed",
            )

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
        self._validate_user_id(user_id)

        if not source.strip():
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

        await self.users.get_by_id_for_update(
            user_id
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

        if not source.strip():
            raise ValueError(
                "Reward source cannot be empty."
            )

        currency = currency.quantize(
            Decimal("0.01")
        )

        progression = None

        if xp > 0:
            user = await self.users.add_xp(
                user_id=user_id,
                amount=xp,
            )

            if user is None:
                raise ValueError(
                    f"User {user_id} does not exist."
                )

            progression = ProgressionService(
                self.users.session
            )

            await progression.add_xp(
                user_id=user_id,
                amount=xp,
            )

        if gems > 0:
            await self.economy.add_gems(
                user_id=user_id,
                amount=gems,
            )

        if xp > 0:
            user = await self.users.add_xp(
                user_id=user_id,
                amount=xp,
            )

            if user is None:
                raise ValueError(
                    f"User {user_id} does not exist."
                )

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
            reason=(
                None
                if rewarded
                else "empty_reward"
            ),
        )
