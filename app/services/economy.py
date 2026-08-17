"""
Economy service.

Содержит бизнес-логику экономики проекта.

Отвечает за:
    - баланс пользователей;
    - переводы;
    - начисления;
    - списания;
    - гемы;
    - административные корректировки;
    - историю транзакций.

ВАЖНО:

Service НЕ работает с SQLAlchemy напрямую.

Он использует:
    EconomyRepository

Repository отвечает за БД.
Service отвечает за бизнес-правила.

commit() / rollback() выполняются выше уровня сервиса
через общую транзакцию приложения.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from app.database.repositories.economy import EconomyRepository
from app.database.models.economy import Transaction, Wallet


class EconomyService:
    """
    Сервис экономики пользователя.
    """

    def __init__(
        self,
        repository: EconomyRepository,
    ) -> None:
        self.repository = repository

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    @staticmethod
    def normalize_amount(
        amount: Decimal | int | float | str,
    ) -> Decimal:
        """
        Нормализовать денежное значение.

        Все денежные операции в сервисе работают
        с двумя знаками после запятой.
        """

        return EconomyRepository.normalize_amount(
            amount
        )

    @staticmethod
    def validate_positive_amount(
        amount: Decimal | int | float | str,
    ) -> Decimal:
        """
        Проверить, что сумма положительная.
        """

        amount = EconomyService.normalize_amount(
            amount
        )

        if amount <= 0:
            raise ValueError(
                "Amount must be greater than zero."
            )

        return amount

    # ========================================================================
    # WALLET
    # ========================================================================

    async def get_wallet(
        self,
        user_id: int,
    ) -> Wallet:
        """
        Получить кошелёк пользователя.

        Если кошелька нет — он создаётся.
        """

        if user_id <= 0:
            raise ValueError(
                "Invalid user_id."
            )

        return await self.repository.get_or_create_wallet(
            user_id
        )

    async def get_balance(
        self,
        user_id: int,
    ) -> Decimal:
        """
        Получить баланс пользователя.
        """

        if user_id <= 0:
            raise ValueError(
                "Invalid user_id."
            )

        return await self.repository.get_balance(
            user_id
        )

    async def get_gems(
        self,
        user_id: int,
    ) -> int:
        """
        Получить количество гемов пользователя.
        """

        if user_id <= 0:
            raise ValueError(
                "Invalid user_id."
            )

        return await self.repository.get_gems(
            user_id
        )

    # ========================================================================
    # ADD BALANCE
    # ========================================================================

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
        """
        Начислить пользователю деньги.

        Это основной метод для любых доходов.

        Например:

            сообщение
            награда
            выигрыш
            продажа предмета
            ежедневная награда
            часовая награда
        """

        if user_id <= 0:
            raise ValueError(
                "Invalid user_id."
            )

        amount = self.validate_positive_amount(
            amount
        )

        if not source or not source.strip():
            raise ValueError(
                "Transaction source cannot be empty."
            )

        if not transaction_type or not transaction_type.strip():
            raise ValueError(
                "Transaction type cannot be empty."
            )

        return await self.repository.add_balance(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type.strip(),
            source=source.strip(),
            related_user_id=related_user_id,
            reference_id=reference_id,
            metadata_json=metadata_json,
        )

    # ========================================================================
    # REMOVE BALANCE
    # ========================================================================

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
        """
        Списать деньги у пользователя.

        Возвращает:
            Transaction — если успешно;
            None — если недостаточно средств.
        """

        if user_id <= 0:
            raise ValueError(
                "Invalid user_id."
            )

        amount = self.validate_positive_amount(
            amount
        )

        if not source or not source.strip():
            raise ValueError(
                "Transaction source cannot be empty."
            )

        if not transaction_type or not transaction_type.strip():
            raise ValueError(
                "Transaction type cannot be empty."
            )

        return await self.repository.remove_balance(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type.strip(),
            source=source.strip(),
            related_user_id=related_user_id,
            reference_id=reference_id,
            metadata_json=metadata_json,
        )

    # ========================================================================
    # CHECK BALANCE
    # ========================================================================

    async def has_money(
        self,
        *,
        user_id: int,
        amount: Decimal | int | float | str,
    ) -> bool:
        """
        Проверить наличие необходимой суммы.
        """

        amount = self.validate_positive_amount(
            amount
        )

        balance = await self.get_balance(
            user_id
        )

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
        """
        Перевести деньги между пользователями.

        Возвращает:

            (
                транзакция отправителя,
                транзакция получателя,
            )

        При недостатке средств выбрасывается ValueError.

        Почему здесь, а не в handler:

        Handler должен только получить Telegram-команду
        и передать данные сервису.

        Правило "нельзя перевести больше своего баланса"
        является бизнес-логикой и находится здесь.
        """

        if sender_id <= 0:
            raise ValueError(
                "Invalid sender_id."
            )

        if receiver_id <= 0:
            raise ValueError(
                "Invalid receiver_id."
            )

        if sender_id == receiver_id:
            raise ValueError(
                "Cannot transfer money to yourself."
            )

        amount = self.validate_positive_amount(
            amount
        )

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
    # GEMS
    # ========================================================================

    async def add_gems(
        self,
        *,
        user_id: int,
        amount: int,
        source: str = "system",
    ) -> Wallet:
        """
        Начислить гемы.

        source пока является параметром сервиса,
        чтобы позже можно было добавить отдельный
        журнал операций с гемами.
        """

        if user_id <= 0:
            raise ValueError(
                "Invalid user_id."
            )

        if amount <= 0:
            raise ValueError(
                "Gem amount must be greater than zero."
            )

        if not source or not source.strip():
            raise ValueError(
                "Gem source cannot be empty."
            )

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
        """
        Списать гемы.

        False означает недостаток гемов.
        """

        if user_id <= 0:
            raise ValueError(
                "Invalid user_id."
            )

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
        """
        Проверить наличие гемов.
        """

        if amount <= 0:
            raise ValueError(
                "Gem amount must be greater than zero."
            )

        gems = await self.get_gems(
            user_id
        )

        return gems >= amount

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
        """
        Универсальное начисление награды.

        Это удобная точка входа для других сервисов.

        Например:

            EconomyService.reward(
                user_id=user_id,
                amount=5,
                source="message",
            )

        Или:

            source="hourly_reward"
            source="daily_reward"
            source="case_reward"
            source="game_win"
        """

        return await self.add_money(
            user_id=user_id,
            amount=amount,
            source=source,
            transaction_type="reward",
            reference_id=reference_id,
            metadata_json=metadata_json,
        )

    # ========================================================================
    # PURCHASE
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

        Используется магазинами, играми и командами.

        Например:

            charge(
                user_id=user_id,
                amount=100,
                source="duel",
            )

        При недостатке средств выбрасывается ValueError.
        """

        transaction = await self.remove_money(
            user_id=user_id,
            amount=amount,
            source=source,
            transaction_type="expense",
            reference_id=reference_id,
            metadata_json=metadata_json,
        )

        if transaction is None:
            raise ValueError(
                "Insufficient balance."
            )

        return transaction

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
        Административно изменить баланс.

        amount > 0:
            начисление.

        amount < 0:
            списание.

        amount == 0:
            запрещено.
        """

        if user_id <= 0:
            raise ValueError(
                "Invalid user_id."
            )

        amount = self.normalize_amount(
            amount
        )

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
    # TRANSACTION HISTORY
    # ========================================================================

    async def get_transactions(
        self,
        *,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Transaction]:
        """
        Получить историю финансовых операций.
        """

        if user_id <= 0:
            raise ValueError(
                "Invalid user_id."
            )

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
        """
        Получить конкретную транзакцию.
        """

        if transaction_id <= 0:
            raise ValueError(
                "Invalid transaction_id."
            )

        return await self.repository.get_transaction(
            transaction_id
        )