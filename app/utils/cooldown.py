from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Hashable


# ============================================================================
# COOLDOWN ENTRY
# ============================================================================


@dataclass(slots=True)
class CooldownEntry:
    """
    Одна запись cooldown.

    expires_at:
        Unix timestamp, до которого действие запрещено.
    """

    expires_at: float


# ============================================================================
# COOLDOWN MANAGER
# ============================================================================


class CooldownManager:
    """
    Универсальный менеджер временных ограничений.

    Можно использовать для:

        - игровых команд;
        - /reward;
        - способностей;
        - взаимодействий;
        - антифлуда;
        - других временных ограничений.

    Ключ может состоять из чего угодно:

        ("reward", user_id)
        ("roulette", user_id)
        ("ability", user_id, ability_id)
        ("message", chat_id, user_id)
    """

    def __init__(self) -> None:
        self._cooldowns: dict[
            Hashable,
            CooldownEntry,
        ] = {}

        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # SET
    # ------------------------------------------------------------------

    async def set(
        self,
        key: Hashable,
        seconds: float,
    ) -> None:
        """
        Устанавливает cooldown.

        seconds <= 0:
            cooldown не устанавливается.
        """

        if seconds <= 0:
            return

        expires_at = time.monotonic() + seconds

        async with self._lock:
            self._cooldowns[key] = CooldownEntry(
                expires_at=expires_at,
            )

    # ------------------------------------------------------------------
    # CHECK
    # ------------------------------------------------------------------

    async def is_on_cooldown(
        self,
        key: Hashable,
    ) -> bool:
        """
        Проверяет, действует ли cooldown.
        """

        async with self._lock:
            entry = self._cooldowns.get(key)

            if entry is None:
                return False

            if entry.expires_at <= time.monotonic():
                del self._cooldowns[key]
                return False

            return True

    # ------------------------------------------------------------------
    # REMAINING
    # ------------------------------------------------------------------

    async def remaining(
        self,
        key: Hashable,
    ) -> float:
        """
        Возвращает оставшееся время cooldown.

        Если cooldown отсутствует:
            0.0
        """

        async with self._lock:
            entry = self._cooldowns.get(key)

            if entry is None:
                return 0.0

            remaining = (
                entry.expires_at
                - time.monotonic()
            )

            if remaining <= 0:
                del self._cooldowns[key]
                return 0.0

            return remaining

    # ------------------------------------------------------------------
    # READY
    # ------------------------------------------------------------------

    async def is_ready(
        self,
        key: Hashable,
    ) -> bool:
        """
        Обратная проверка:

            True  -> действие доступно
            False -> cooldown активен
        """

        return not await self.is_on_cooldown(key)

    # ------------------------------------------------------------------
    # CLEAR
    # ------------------------------------------------------------------

    async def clear(
        self,
        key: Hashable,
    ) -> None:
        """
        Удаляет cooldown вручную.
        """

        async with self._lock:
            self._cooldowns.pop(
                key,
                None,
            )

    # ------------------------------------------------------------------
    # CLEAR ALL
    # ------------------------------------------------------------------

    async def clear_all(self) -> None:
        """
        Полностью очищает менеджер.
        """

        async with self._lock:
            self._cooldowns.clear()

    # ------------------------------------------------------------------
    # CLEANUP
    # ------------------------------------------------------------------

    async def cleanup(self) -> int:
        """
        Удаляет истёкшие cooldown.

        Возвращает количество удалённых записей.
        """

        now = time.monotonic()

        async with self._lock:
            expired_keys = [
                key
                for key, entry
                in self._cooldowns.items()
                if entry.expires_at <= now
            ]

            for key in expired_keys:
                del self._cooldowns[key]

        return len(expired_keys)

    # ------------------------------------------------------------------
    # SIZE
    # ------------------------------------------------------------------

    async def size(self) -> int:
        """
        Возвращает количество активных записей.
        """

        await self.cleanup()

        async with self._lock:
            return len(self._cooldowns)


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

cooldowns = CooldownManager()