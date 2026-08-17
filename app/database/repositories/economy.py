from __future__ import annotations

import asyncio
from decimal import Decimal, InvalidOperation
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.economy import Transaction, Wallet


class EconomyRepository:
    """
    Репозиторий экономики.

    ВАЖНО:

    - commit() здесь не выполняется;
    - commit/rollback выполняет внешний middleware;
    - все изменения кошельков сериализуются одним asyncio.Lock;
    - это особенно важно для SQLite;
    - финансовые операции поддерживают reference_id для
      защиты от повторного выполнения.

    Архитектура рассчитана на один постоянно работающий
    процесс бота.

    При текущем ограничении:

        максимум 5 чатов;
        максимум 50 пользователей в каждом;
        максимум ~250 пользователей.

    Отдельный Redis / distributed lock здесь не нужен.
    """

    _mutation_lock = asyncio.Lock()

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # ========================================================================
    # INTERNAL
    # ========================================================================

    @staticmethod
    def normalize_amount(
        amount: Decimal | int | float | str,
    ) -> Decimal:
        """
        Привести денежное значение к Decimal с двумя знаками.
        """

        try:
            if isinstance(amount, Decimal):
                result = amount
            else:
                result = Decimal(str(amount))
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "Amount must be a valid number."
            ) from exc

        if not result.is_finite():
            raise ValueError(
                "Amount must be a finite number."
            )

        try:
            result = result.quantize(
                Decimal("0.01")
            )
        except InvalidOperation as exc:
            raise ValueError(
                "Amount is too large or has invalid precision."
            ) from exc

        return result

    async def _find_reference(
        self,
        *,
        user_id: int,
        reference_id: str | None,
    ) -> Transaction | None:
        """
        Найти уже выполненную операцию.

        reference_id уникален в рамках пользователя.

        Для transfer один и тот же reference_id
        используется у двух пользователей.
        """

        if reference_id is None:
            return None

        reference_id = reference_id.strip()

        if not reference_id:
            return None

        result = await self.session.execute(
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.reference_id == reference_id,
            )
            .order_by(
                Transaction.id.desc()
            )
            .limit(1)
        )

        return result.scalar_one_or_none()

    @staticmethod
    def _validate_existing_transaction(
        transaction: Transaction,
        *,
        expected_amount: Decimal,
        transaction_type: str,
        source: str,
        related_user_id: int | None,
    ) -> None:
        """
        Проверить, что найденная транзакция действительно
        соответствует повторяемой бизнес-операции.

        Это критично для idempotency.

        Например:

            первый вызов:
                reference_id = reward:123
                amount = 100

            второй вызов:
                reference_id = reward:123
                amount = 1000

        Второй вызов не должен молча получить
        транзакцию первого вызова.
        """

        existing_amount = Decimal(
            str(transaction.amount)
        )

        if existing_amount != expected_amount:
            raise RuntimeError(
                "Transaction reference collision: "
                "amount does not match existing transaction."
            )

        if transaction.transaction_type != transaction_type:
            raise RuntimeError(
                "Transaction reference collision: "
                "transaction_type does not match existing transaction."
            )

        if transaction.source != source:
            raise RuntimeError(
                "Transaction reference collision: "
                "source does not match existing transaction."
            )

        if (
            transaction.related_user_id
            != related_user_id
        ):
            raise RuntimeError(
                "Transaction reference collision: "
                "related_user_id does not match existing transaction."
            )

    @staticmethod
    def _normalize_reference(
        reference_id: str | None,
    ) -> str | None:
        """
        Нормализовать reference_id.

        Пустая строка считается отсутствующим reference_id.
        """

        if reference_id is None:
            return None

        reference_id = reference_id.strip()

        if not reference_id:
            return None

        if len(reference_id) > 255:
            raise ValueError(
                "reference_id cannot be longer than 255 characters."
            )

        return reference_id

    # ========================================================================
    # WALLET
    # ========================================================================

    async def get_wallet(
        self,
        user_id: int,
        *,
        for_update: bool = False,
    ) -> Wallet | None:
        """
        Получить кошелёк пользователя.

        На PostgreSQL for_update=True использует
        row-level locking.

        На SQLite SELECT FOR UPDATE не является
        полноценной блокировкой, поэтому операции
        изменения дополнительно защищены _mutation_lock.
        """

        query = select(Wallet).where(
            Wallet.user_id == user_id,
        )

        if for_update:
            bind = self.session.get_bind()

            if bind.dialect.name != "sqlite":
                query = query.with_for_update()

        result = await self.session.execute(
            query
        )

        return result.scalar_one_or_none()

    async def get_or_create_wallet(
        self,
        user_id: int,
        *,
        for_update: bool = False,
    ) -> Wallet:
        """
        Получить кошелёк или создать новый.

        Внутри mutation-операций этот метод вызывается
        под _mutation_lock.
        """

        wallet = await self.get_wallet(
            user_id,
            for_update=for_update,
        )

        if wallet is not None:
            return wallet

        wallet = Wallet(
            user_id=user_id,
            balance=Decimal("0.00"),
            gems=0,
        )

        self.session.add(wallet)

        await self.session.flush()

        return wallet

    # ========================================================================
    # BALANCE
    # ========================================================================

    async def get_balance(
        self,
        user_id: int,
    ) -> Decimal:
        wallet = await self.get_wallet(
            user_id
        )

        if wallet is None:
            return Decimal("0.00")

        return wallet.balance

    async def set_balance(
        self,
        user_id: int,
        amount: Decimal | int | float | str,
    ) -> Wallet:
        """
        Прямо установить баланс.

        Использовать только для административных/
        служебных операций.

        Для обычных финансовых изменений использовать
        add_balance/remove_balance, чтобы сохранялась
        история Transaction.
        """

        amount = self.normalize_amount(
            amount
        )

        if amount < 0:
            raise ValueError(
                "Balance cannot be negative."
            )

        async with self._mutation_lock:
            wallet = await self.get_or_create_wallet(
                user_id,
                for_update=True,
            )

            wallet.balance = amount

            await self.session.flush()

            return wallet

    # ========================================================================
    # ADD MONEY
    # ========================================================================

    async def add_balance(
        self,
        *,
        user_id: int,
        amount: Decimal | int | float | str,
        transaction_type: str,
        source: str,
        related_user_id: int | None = None,
        reference_id: str | None = None,
        metadata_json: str | None = None,
    ) -> Transaction:
        """
        Начислить деньги.

        reference_id обеспечивает idempotency.

        Если reference_id уже существует:

            - возвращается существующая транзакция,
            - но перед этим проверяется, что она соответствует
              текущей операции.

        Поэтому один reference_id нельзя использовать
        для другой финансовой операции.
        """

        amount = self.normalize_amount(
            amount
        )

        if amount <= 0:
            raise ValueError(
                "add_balance amount must be greater than zero."
            )

        if not transaction_type:
            raise ValueError(
                "transaction_type cannot be empty."
            )

        if not source:
            raise ValueError(
                "source cannot be empty."
            )

        reference_id = self._normalize_reference(
            reference_id
        )

        async with self._mutation_lock:

            # ----------------------------------------------------------------
            # IDEMPOTENCY
            # ----------------------------------------------------------------

            existing = await self._find_reference(
                user_id=user_id,
                reference_id=reference_id,
            )

            if existing is not None:
                self._validate_existing_transaction(
                    existing,
                    expected_amount=amount,
                    transaction_type=transaction_type,
                    source=source,
                    related_user_id=related_user_id,
                )

                return existing

            # ----------------------------------------------------------------
            # WALLET
            # ----------------------------------------------------------------

            wallet = await self.get_or_create_wallet(
                user_id,
                for_update=True,
            )

            balance_before = wallet.balance
            balance_after = (
                balance_before + amount
            )

            wallet.balance = balance_after

            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                transaction_type=transaction_type,
                source=source,
                related_user_id=related_user_id,
                reference_id=reference_id,
                metadata_json=metadata_json,
            )

            self.session.add(
                transaction
            )

            await self.session.flush()

            return transaction

    # ========================================================================
    # REMOVE MONEY
    # ========================================================================

    async def remove_balance(
        self,
        *,
        user_id: int,
        amount: Decimal | int | float | str,
        transaction_type: str,
        source: str,
        related_user_id: int | None = None,
        reference_id: str | None = None,
        metadata_json: str | None = None,
    ) -> Transaction | None:
        """
        Списать деньги.

        При недостатке средств возвращает None.

        При повторном reference_id возвращает
        существующую транзакцию после проверки
        её соответствия текущей операции.
        """

        amount = self.normalize_amount(
            amount
        )

        if amount <= 0:
            raise ValueError(
                "remove_balance amount must be greater than zero."
            )

        if not transaction_type:
            raise ValueError(
                "transaction_type cannot be empty."
            )

        if not source:
            raise ValueError(
                "source cannot be empty."
            )

        reference_id = self._normalize_reference(
            reference_id
        )

        async with self._mutation_lock:

            # ----------------------------------------------------------------
            # IDEMPOTENCY
            # ----------------------------------------------------------------

            existing = await self._find_reference(
                user_id=user_id,
                reference_id=reference_id,
            )

            if existing is not None:
                self._validate_existing_transaction(
                    existing,
                    expected_amount=-amount,
                    transaction_type=transaction_type,
                    source=source,
                    related_user_id=related_user_id,
                )

                return existing

            # ----------------------------------------------------------------
            # WALLET
            # ----------------------------------------------------------------

            wallet = await self.get_or_create_wallet(
                user_id,
                for_update=True,
            )

            if wallet.balance < amount:
                return None

            balance_before = wallet.balance
            balance_after = (
                balance_before - amount
            )

            wallet.balance = balance_after

            transaction = Transaction(
                user_id=user_id,
                amount=-amount,
                balance_before=balance_before,
                balance_after=balance_after,
                transaction_type=transaction_type,
                source=source,
                related_user_id=related_user_id,
                reference_id=reference_id,
                metadata_json=metadata_json,
            )

            self.session.add(
                transaction
            )

            await self.session.flush()

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
        transaction_type: str = "transfer",
        source: str = "user_transfer",
        reference_id: str | None = None,
        metadata_json: str | None = None,
    ) -> tuple[Transaction, Transaction] | None:
        """
        Атомарный перевод между двумя пользователями.

        Внутри одного процесса операции сериализуются
        через _mutation_lock.

        На PostgreSQL дополнительно используются
        row-level locks.

        На SQLite основной механизм защиты —
        _mutation_lock.

        Один reference_id используется одновременно
        для sender и receiver.

        Повторный вызов возвращает обе существующие
        транзакции только если ОБЕ операции полностью
        соответствуют исходной.
        """

        amount = self.normalize_amount(
            amount
        )

        if amount <= 0:
            raise ValueError(
                "Transfer amount must be greater than zero."
            )

        if sender_id == receiver_id:
            raise ValueError(
                "Sender and receiver cannot be the same user."
            )

        if not transaction_type:
            raise ValueError(
                "transaction_type cannot be empty."
            )

        if not source:
            raise ValueError(
                "source cannot be empty."
            )

        reference_id = self._normalize_reference(
            reference_id
        )

        async with self._mutation_lock:

            # ----------------------------------------------------------------
            # IDEMPOTENCY
            # ----------------------------------------------------------------

            sender_existing = await self._find_reference(
                user_id=sender_id,
                reference_id=reference_id,
            )

            receiver_existing = await self._find_reference(
                user_id=receiver_id,
                reference_id=reference_id,
            )

            if (
                sender_existing is not None
                and receiver_existing is not None
            ):
                self._validate_existing_transaction(
                    sender_existing,
                    expected_amount=-amount,
                    transaction_type=transaction_type,
                    source=source,
                    related_user_id=receiver_id,
                )

                self._validate_existing_transaction(
                    receiver_existing,
                    expected_amount=amount,
                    transaction_type=transaction_type,
                    source=source,
                    related_user_id=sender_id,
                )

                return (
                    sender_existing,
                    receiver_existing,
                )

            # Если существует только одна сторона,
            # операция находится в неконсистентном состоянии.

            if (
                sender_existing is not None
                or receiver_existing is not None
            ):
                raise RuntimeError(
                    "Transfer reference already exists "
                    "for only one side of the transaction."
                )

            # ----------------------------------------------------------------
            # LOCK ORDER
            # ----------------------------------------------------------------

            first_id = min(
                sender_id,
                receiver_id,
            )

            second_id = max(
                sender_id,
                receiver_id,
            )

            first_wallet = (
                await self.get_or_create_wallet(
                    first_id,
                    for_update=True,
                )
            )

            second_wallet = (
                await self.get_or_create_wallet(
                    second_id,
                    for_update=True,
                )
            )

            if sender_id == first_id:
                sender_wallet = first_wallet
                receiver_wallet = second_wallet
            else:
                sender_wallet = second_wallet
                receiver_wallet = first_wallet

            # ----------------------------------------------------------------
            # BALANCE CHECK
            # ----------------------------------------------------------------

            if sender_wallet.balance < amount:
                return None

            # ----------------------------------------------------------------
            # SENDER
            # ----------------------------------------------------------------

            sender_before = (
                sender_wallet.balance
            )

            sender_after = (
                sender_before - amount
            )

            sender_wallet.balance = (
                sender_after
            )

            sender_transaction = Transaction(
                user_id=sender_id,
                amount=-amount,
                balance_before=sender_before,
                balance_after=sender_after,
                transaction_type=transaction_type,
                source=source,
                related_user_id=receiver_id,
                reference_id=reference_id,
                metadata_json=metadata_json,
            )

            # ----------------------------------------------------------------
            # RECEIVER
            # ----------------------------------------------------------------

            receiver_before = (
                receiver_wallet.balance
            )

            receiver_after = (
                receiver_before + amount
            )

            receiver_wallet.balance = (
                receiver_after
            )

            receiver_transaction = Transaction(
                user_id=receiver_id,
                amount=amount,
                balance_before=receiver_before,
                balance_after=receiver_after,
                transaction_type=transaction_type,
                source=source,
                related_user_id=sender_id,
                reference_id=reference_id,
                metadata_json=metadata_json,
            )

            self.session.add_all(
                [
                    sender_transaction,
                    receiver_transaction,
                ]
            )

            await self.session.flush()

            return (
                sender_transaction,
                receiver_transaction,
            )

    # ========================================================================
    # GEMS
    # ========================================================================

    async def get_gems(
        self,
        user_id: int,
    ) -> int:
        wallet = await self.get_wallet(
            user_id
        )

        if wallet is None:
            return 0

        return wallet.gems

    async def add_gems(
        self,
        *,
        user_id: int,
        amount: int,
    ) -> Wallet:
        if amount <= 0:
            raise ValueError(
                "Gem amount must be greater than zero."
            )

        async with self._mutation_lock:
            wallet = await self.get_or_create_wallet(
                user_id,
                for_update=True,
            )

            wallet.gems += amount

            await self.session.flush()

            return wallet

    async def remove_gems(
        self,
        *,
        user_id: int,
        amount: int,
    ) -> bool:
        if amount <= 0:
            raise ValueError(
                "Gem amount must be greater than zero."
            )

        async with self._mutation_lock:
            wallet = await self.get_or_create_wallet(
                user_id,
                for_update=True,
            )

            if wallet.gems < amount:
                return False

            wallet.gems -= amount

            await self.session.flush()

            return True

    # ========================================================================
    # TRANSACTION HISTORY
    # ========================================================================

    async def get_transactions(
        self,
        user_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Transaction]:
        limit = max(
            1,
            min(limit, 500),
        )

        offset = max(
            0,
            offset,
        )

        result = await self.session.execute(
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
            )
            .order_by(
                Transaction.created_at.desc(),
                Transaction.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return result.scalars().all()

    async def get_transaction(
        self,
        transaction_id: int,
    ) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction).where(
                Transaction.id == transaction_id,
            )
        )

        return result.scalar_one_or_none()

    # ========================================================================
    # ADMIN
    # ========================================================================

    async def admin_adjust_balance(
        self,
        *,
        user_id: int,
        amount: Decimal | int | float | str,
        source: str = "admin",
        reference_id: str | None = None,
        metadata_json: str | None = None,
    ) -> Transaction:
        """
        Административное изменение баланса.

        Положительное значение:
            начисление.

        Отрицательное значение:
            списание.
        """

        amount = self.normalize_amount(
            amount
        )

        if amount == 0:
            raise ValueError(
                "Administrative balance adjustment cannot be zero."
            )

        if amount > 0:
            return await self.add_balance(
                user_id=user_id,
                amount=amount,
                transaction_type="admin_adjustment",
                source=source,
                reference_id=reference_id,
                metadata_json=metadata_json,
            )

        transaction = await self.remove_balance(
            user_id=user_id,
            amount=abs(amount),
            transaction_type="admin_adjustment",
            source=source,
            reference_id=reference_id,
            metadata_json=metadata_json,
        )

        if transaction is None:
            raise ValueError(
                "User does not have enough balance "
                "for administrative deduction."
            )

        return transaction


__all__ = [
    "EconomyRepository",
]