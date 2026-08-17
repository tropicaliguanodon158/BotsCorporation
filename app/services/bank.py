"""
Bank service.

Бизнес-логика банковских операций.

Repository:
    EconomyRepository

Service отвечает за:
    - баланс;
    - переводы;
    - пополнение;
    - списание;
    - административные корректировки.

commit()/rollback() здесь не выполняются.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.database.repositories.economy import EconomyRepository


@dataclass(slots=True)
class BalanceResult:
    user_id: int
    balance: Decimal


@dataclass(slots=True)
class TransferResult:
    sender_id: int
    receiver_id: int
    amount: Decimal
    success: bool
    reason: str | None = None


class BankService:
    """
    Сервис банковской системы.
    """

    def __init__(
        self,
        *,
        economy_repository: EconomyRepository,
    ) -> None:
        self.economy = economy_repository

    # ========================================================================
    # BALANCE
    # ========================================================================

    async def get_balance(
        self,
        *,
        user_id: int,
    ) -> BalanceResult:
        self._validate_user_id(user_id)

        balance = await self.economy.get_balance(user_id)

        return BalanceResult(
            user_id=user_id,
            balance=balance,
        )

    # ========================================================================
    # DEPOSIT / ADD
    # ========================================================================

    async def deposit(
        self,
        *,
        user_id: int,
        amount: Decimal | int | float | str,
        source: str = "bank_deposit",
        reference_id: str | None = None,
    ):
        self._validate_user_id(user_id)

        amount = self._normalize_amount(amount)

        if amount <= 0:
            raise ValueError(
                "Deposit amount must be greater than zero."
            )

        return await self.economy.add_balance(
            user_id=user_id,
            amount=amount,
            transaction_type="deposit",
            source=source,
            reference_id=reference_id,
        )

    # ========================================================================
    # WITHDRAW
    # ========================================================================

    async def withdraw(
        self,
        *,
        user_id: int,
        amount: Decimal | int | float | str,
        source: str = "bank_withdraw",
        reference_id: str | None = None,
    ):
        self._validate_user_id(user_id)

        amount = self._normalize_amount(amount)

        if amount <= 0:
            raise ValueError(
                "Withdrawal amount must be greater than zero."
            )

        transaction = await self.economy.remove_balance(
            user_id=user_id,
            amount=amount,
            transaction_type="withdraw",
            source=source,
            reference_id=reference_id,
        )

        if transaction is None:
            raise ValueError(
                "Insufficient balance."
            )

        return transaction

    # ========================================================================
    # TRANSFER
    # ========================================================================

    async def transfer(
        self,
        *,
        sender_id: int,
        receiver_id: int,
        amount: Decimal | int | float | str,
        source: str = "user_transfer",
        reference_id: str | None = None,
    ) -> TransferResult:
        self._validate_user_id(sender_id)
        self._validate_user_id(receiver_id)

        if sender_id == receiver_id:
            return TransferResult(
                sender_id=sender_id,
                receiver_id=receiver_id,
                amount=Decimal("0.00"),
                success=False,
                reason="same_user",
            )

        amount = self._normalize_amount(amount)

        if amount <= 0:
            return TransferResult(
                sender_id=sender_id,
                receiver_id=receiver_id,
                amount=amount,
                success=False,
                reason="invalid_amount",
            )

        result = await self.economy.transfer(
            sender_id=sender_id,
            receiver_id=receiver_id,
            amount=amount,
            transaction_type="transfer",
            source=source,
            reference_id=reference_id,
        )

        if result is None:
            return TransferResult(
                sender_id=sender_id,
                receiver_id=receiver_id,
                amount=amount,
                success=False,
                reason="insufficient_balance",
            )

        return TransferResult(
            sender_id=sender_id,
            receiver_id=receiver_id,
            amount=amount,
            success=True,
        )

    # ========================================================================
    # GEMS
    # ========================================================================

    async def get_gems(
        self,
        *,
        user_id: int,
    ) -> int:
        self._validate_user_id(user_id)

        return await self.economy.get_gems(user_id)

    async def add_gems(
        self,
        *,
        user_id: int,
        amount: int,
    ):
        self._validate_user_id(user_id)

        if amount <= 0:
            raise ValueError(
                "Gem amount must be greater than zero."
            )

        return await self.economy.add_gems(
            user_id=user_id,
            amount=amount,
        )

    async def remove_gems(
        self,
        *,
        user_id: int,
        amount: int,
    ) -> bool:
        self._validate_user_id(user_id)

        if amount <= 0:
            raise ValueError(
                "Gem amount must be greater than zero."
            )

        return await self.economy.remove_gems(
            user_id=user_id,
            amount=amount,
        )

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def _validate_user_id(
        user_id: int,
    ) -> None:
        if user_id <= 0:
            raise ValueError(
                "Invalid user_id."
            )

    @staticmethod
    def _normalize_amount(
        amount: Decimal | int | float | str,
    ) -> Decimal:
        if isinstance(amount, Decimal):
            value = amount
        else:
            value = Decimal(str(amount))

        return value.quantize(
            Decimal("0.01")
        )