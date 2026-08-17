```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

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

    Отвечает за:
        - награды за сообщения;
        - фото;
        - видео;
        - hourly;
        - daily;
        - произвольные награды.

    ВАЖНО:
        Сервис не выполняет commit().
        Транзакцией управляет внешний слой приложения.
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
    def _normalize_datetime(value: datetime) -> datetime:
        if value.tzinfo is not None:
            return value.replace(tzinfo=None)

        return value

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

        return result.quantize(Decimal("0.01"))

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
        Проверяет финансовую историю пользователя.

        Это защита от повторной выдачи после уже сохранённой
        транзакции. Внешняя транзакция БД всё равно должна
        использоваться для полной защиты от race condition.
        """

        transactions = await self.economy.get_transactions(
            user_id=user_id,
            limit=100,
            offset=0,
        )

        since = self._normalize_datetime(since)

        for transaction in transactions:
            if transaction.source != source:
                continue

            created_at = self._normalize_datetime(
                transaction.created_at,
            )

            if created_at >= since:
                return True

        return False

    async def _already_claimed_today(
        self,
        *,
        user_id: int,
        source: str,
    ) -> bool:
        now = self._now()

        start_of_day = datetime(
            now.year,
            now.month,
            now.day,
        )

        return await self._has_recent_transaction(
            user_id=user_id,
            source=source,
            since=start_of_day,
        )

    async def _already_claimed_hourly(
        self,
        *,
        user_id: int,
    ) -> bool:
        return await self._has_recent_transaction(
            user_id=user_id,
            source="hourly_reward",
            since=self._now() - timedelta(hours=1),
        )

    async def _message_on_cooldown(
        self,
        *,
        user_id: int,
        cooldown_seconds: int,
    ) -> bool:
        if cooldown_seconds <= 0:
            return False

        return await self._has_recent_transaction(
            user_id=user_id,
            source="message",
            since=self._now()
            - timedelta(seconds=cooldown_seconds),
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

        if message_type not in {"text", "other"}:
            message_type = "text"

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

        if await self._message_on_cooldown(
            user_id=user_id,
            cooldown_seconds=cooldown,
        ):
            return RewardResult(
                user_id=user_id,
                chat_id=chat_id,
                source="message",
                rewarded=False,
                reason="cooldown",
            )

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
        self._validate_user_id(user_id)

        if await self._already_claimed_hourly(
            user_id=user_id,
        ):
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
        self._validate_user_id(user_id)

        if await self._already_claimed_today(
            user_id=user_id,
            source="daily_reward",
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

        if not source or not source.strip():
            raise ValueError("Reward source cannot be empty.")

        currency = self._decimal(currency)
        xp = self._int(xp)
        gems = self._int(gems)

        if currency < 0:
            raise ValueError("Currency reward cannot be negative.")

        if xp < 0:
            raise ValueError("XP reward cannot be negative.")

        if gems < 0:
            raise ValueError("Gem reward cannot be negative.")

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
            raise ValueError("Currency reward cannot be negative.")

        if xp < 0:
            raise ValueError("XP reward cannot be negative.")

        if gems < 0:
            raise ValueError("Gem reward cannot be negative.")

        if not source or not source.strip():
            raise ValueError("Reward source cannot be empty.")

        source = source.strip()

        if currency > 0:
            await self.economy.add_balance(
                user_id=user_id,
                amount=currency,
                transaction_type="reward",
                source=source,
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
            reason=None if rewarded else "empty_reward",
        )
```
