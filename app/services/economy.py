```python
"""
Economy service.

Содержит бизнес-логику экономики проекта.

Service не работает с SQLAlchemy напрямую.
Все операции с БД выполняются через EconomyRepository.

commit / rollback выполняются уровнем выше.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from app.database.models.economy import Transaction, Wallet
from app.database.repositories.economy import EconomyRepository


class EconomyService:
    """Бизнес-логика экономики пользователя."""

    def __init__(self, repository: EconomyRepository) -> None:
        self.repository = repository

    # ========================================================================
    # INTERNAL
    # ========================================================================

    @staticmethod
    def normalize_amount(
        amount: Decimal | int | float | str,
    ) -> Decimal:
        """Нормализовать денежную сумму до двух знаков."""

        return EconomyRepository.normalize_amount(amount)

    @classmethod
    def validate_positive_amount(
        cls,
        amount: Decimal | int | float | str,
    ) -> Decimal:
        """Проверить положительную денежную сумму."""

        normalized = cls.normalize_amount(amount)

        if normalized <= 0:
            raise ValueError(
                "Amount must be greater than zero."
            )

        return normalized

    @staticmethod
    def validate_user_id(user_id: int) -> None:
        if user_id <= 0:
            raise ValueError("Invalid user_id.")

    @staticmethod
    def validate_source(source: str) -> str:
        if not source or not source.strip():
            raise ValueError(
                "Transaction source cannot be empty."
            )

        return source.strip()

    @staticmethod
    def validate_transaction_type(
        transaction_type: str,
    ) -> str:
        if (
            not transaction_type
            or not transaction_type.strip()
        ):
            raise ValueError(
                "Transaction type cannot be empty."
            )

        return transaction_type.strip()

    # ========================================================================
    # WALLET
    # ========================================================================

    async def get_wallet(
        self,
        user_id: int,
    ) -> Wallet:
        """Получить или создать кошелёк."""

        self.validate_user_id(user_id)

        return await self.repository.get_or_create_wallet(
            user_id
        )

    async def get_balance(
        self,
        user_id: int,
    ) -> Decimal:
        """Получить баланс пользователя."""

        self.validate_user_id(user_id)

        return await self.repository.get_balance(
            user_id
        )

    async def get_gems(
        self,
        user_id: int,
    ) -> int:
        """Получить количество гемов."""

        self.validate_user_id(user_id)

        return await self.repository.get_gems(
            user_id
        )

    # ========================================================================
    # ADD BALANCE
    # ========================================================================

    async def add_balance(
        self,
        *,
        user_id: int,
        amount: Decimal | int | float | str,
        transaction_type: str = "income",
        source: str = "system",
        related_user_id: int | None = None,
        reference_id: str | None = None,
        metadata_json: str | None = None,
    ) -> Transaction:
        """
        Начислить деньги.

        Это основной низкоуровневый метод для положительной
        финансовой операции.
        """

        self.validate_user_id(user_id)

        amount = self.validate_positive_amount(amount)
        source = self.validate_source(source)
        transaction_type = self.validate_transaction_type(
            transaction_type
        )

        return await self.repository.add_balance(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            source=source,
            related_user_id=related_user_id,
            reference_id=reference_id,
            metadata_json=metadata_json,
        )

    async def add_money(
        self,
        *,
        user_id: int,
        amount: Decimal | int | float | str,
        source: str,
        transaction_type: str = "income",
        related_user_id: int | None = None,
        reference_id: str | None = None,
        metadata_json: str | None = None,
    ) -> Transaction:
        """Алиас add_balance для более читаемого API."""

        return await self.add_balance(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            source=source,
            related_user_id=related_user_id,
            reference_id=reference_id,
            metadata_json=metadata_json,
        )

    # ========================================================================
    # REMOVE BALANCE
    # ========================================================================

    async def remove_balance(
        self,
        *,
        user_id: int,
        amount: Decimal | int | float | str,
        transaction_type: str = "expense",
        source: str = "system",
        related_user_id: int | None = None,
        reference_id: str | None = None,
        metadata_json: str | None = None,
    ) -> Transaction | None:
        """
        Списать деньги.

        None означает недостаточный баланс.
        """

        self.validate_user_id(user_id)

        amount = self.validate_positive_amount(amount)
        source = self.validate_source(source)
        transaction_type = self.validate_transaction_type(
            transaction_type
        )

        return await self.repository.remove_balance(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            source=source,
            related_user_id=related_user_id,
            reference_id=reference_id,
            metadata_json=metadata_json,
        )

    async def remove_money(
        self,
        *,
        user_id: int,
        amount: Decimal | int | float | str,
        source: str,
        transaction_type: str = "expense",
        related_user_id: int | None = None,
        reference_id: str | None = None,
        metadata_json: str | None = None,
    ) -> Transaction | None:
        """Алиас remove_balance."""

        return await self.remove_balance(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            source=source,
            related_user_id=related_user_id,
            reference_id=reference_id,
            metadata_json=metadata_json,
        )

    # ========================================================================
    # BALANCE CHECK
    # ========================================================================

    async def has_money(
        self,
        *,
        user_id: int,
        amount: Decimal | int | float | str,
    ) -> bool:
        """Проверить наличие необходимой суммы."""

        self.validate_user_id(user_id)

        amount = self.validate_positive_amount(amount)

        balance = await self.get_balance(user_id)

        return balance >= amount

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
        metadata_json: str | None = None,
    ) -> tuple[Transaction, Transaction]:
        """Перевести деньги между пользователями."""

        self.validate_user_id(sender_id)
        self.validate_user_id(receiver_id)

        if sender_id == receiver_id:
            raise ValueError(
                "Cannot transfer money to yourself."
            )

        amount = self.validate_positive_amount(amount)
        source = self.validate_source(source)

        result = await self.repository.transfer(
            sender_id=sender_id,
            receiver_id=receiver_id,
            amount=amount,
            transaction_type="transfer",
            source=source,
            reference_id=reference_id,
            metadata_json=metadata_json,
        )

        if result is None:
            raise ValueError(
                "Insufficient balance."
            )

        return result

    # ========================================================================
    # REWARDS
    # ========================================================================

    async def reward(
        self,
        *,
        user_id: int,
        amount: Decimal | int | float | str,
        source: str,
        reference_id: str | None = None,
        metadata_json: str | None = None,
    ) -> Transaction:
        """Начислить пользователю награду."""

        return await self.add_balance(
            user_id=user_id,
            amount=amount,
            transaction_type="reward",
            source=source,
            reference_id=reference_id,
            metadata_json=metadata_json,
        )

    # ========================================================================
    # CHARGE
    # ========================================================================

    async def charge(
        self,
        *,
        user_id: int,
        amount: Decimal | int | float | str,
        source: str,
        reference_id: str | None = None,
        metadata_json: str | None = None,
    ) -> Transaction:
        """
        Списать деньги за действие.

        При недостатке средств выбрасывается ValueError.
        """

        transaction = await self.remove_balance(
            user_id=user_id,
            amount=amount,
            transaction_type="expense",
            source=source,
            reference_id=reference_id,
            metadata_json=metadata_json,
        )

        if transaction is None:
            raise ValueError(
                "Insufficient balance."
            )

        return transaction

    # ========================================================================
    # GEMS
    # ========================================================================

    async def add_gems(
        self,
        *,
        user_id: int,
        amount: int,
        source: str = "system",
    ) -> Wallet:
        """Начислить гемы."""

        self.validate_user_id(user_id)

        if amount <= 0:
            raise ValueError(
                "Gem amount must be greater than zero."
            )

        self.validate_source(source)

        return await self.repository.add_gems(
            user_id=user_id,
            amount=amount,
        )

    async def remove_gems(
        self,
        *,
        user_id: int,
        amount: int,
    ) -> bool:
        """Списать гемы."""

        self.validate_user_id(user_id)

        if amount <= 0:
            raise ValueError(
                "Gem amount must be greater than zero."
            )

        return await self.repository.remove_gems(
            user_id=user_id,
            amount=amount,
        )

    async def has_gems(
        self,
        *,
        user_id: int,
        amount: int,
    ) -> bool:
        """Проверить наличие гемов."""

        self.validate_user_id(user_id)

        if amount <= 0:
            raise ValueError(
                "Gem amount must be greater than zero."
            )

        gems = await self.get_gems(user_id)

        return gems >= amount

    # ========================================================================
    # ADMIN
    # ========================================================================

    async def admin_adjust_balance(
        self,
        *,
        user_id: int,
        amount: Decimal | int | float | str,
        reference_id: str | None = None,
        metadata_json: str | None = None,
    ) -> Transaction:
        """
        Административная корректировка баланса.

        amount > 0:
            начисление.

        amount < 0:
            списание.
        """

        self.validate_user_id(user_id)

        amount = self.normalize_amount(amount)

        if amount == 0:
            raise ValueError(
                "Adjustment amount cannot be zero."
            )

        return await self.repository.admin_adjust_balance(
            user_id=user_id,
            amount=amount,
            source="admin",
            reference_id=reference_id,
            metadata_json=metadata_json,
        )

    # ========================================================================
    # TRANSACTIONS
    # ========================================================================

    async def get_transactions(
        self,
        *,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Transaction]:
        """Получить историю операций."""

        self.validate_user_id(user_id)

        limit = max(1, min(limit, 500))
        offset = max(0, offset)

        return await self.repository.get_transactions(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    async def get_transaction(
        self,
        transaction_id: int,
    ) -> Transaction | None:
        """Получить конкретную транзакцию."""

        if transaction_id <= 0:
            raise ValueError(
                "Invalid transaction_id."
            )

        return await self.repository.get_transaction(
            transaction_id
        )
```
