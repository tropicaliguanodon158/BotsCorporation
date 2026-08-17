"""
Economy repository.

Отвечает за низкоуровневую работу с кошельками и финансовыми
транзакциями.

ВАЖНО:
    - бизнес-правила находятся в services/economy.py;
    - здесь нет логики рулетки, дуэли, магазина и наград;
    - commit() намеренно не выполняется внутри методов.

Все операции должны выполняться внутри транзакции сервиса.
"""

from decimal import Decimal
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.economy import Transaction, Wallet


class EconomyRepository:
    """
    Репозиторий экономики.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    @staticmethod
    def normalize_amount(amount: Decimal | int | float | str) -> Decimal:
        """
        Приводит денежное значение к Decimal.

        Для финансовых операций float напрямую использовать
        нежелательно из-за особенностей представления чисел.
        """

        if isinstance(amount, Decimal):
            result = amount
        else:
            result = Decimal(str(amount))

        return result.quantize(Decimal("0.01"))

    # ========================================================================
    # WALLET
    # ========================================================================

    async def get_wallet(
        self,
        user_id: int,
    ) -> Wallet | None:
        """
        Получить кошелёк пользователя.
        """

        result = await self.session.execute(
            select(Wallet).where(
                Wallet.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_or_create_wallet(
        self,
        user_id: int,
    ) -> Wallet:
        """
        Получить существующий кошелёк или создать новый.
        """

        wallet = await self.get_wallet(user_id)

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
        """
        Получить баланс пользователя.

        Если кошелька ещё нет — возвращается 0.
        """

        wallet = await self.get_wallet(user_id)

        if wallet is None:
            return Decimal("0.00")

        return wallet.balance

    async def set_balance(
        self,
        user_id: int,
        amount: Decimal | int | float | str,
    ) -> Wallet:
        """
        Установить баланс напрямую.

        Используется только административными/сервисными операциями.

        Обычные операции должны использовать add_balance() или
        remove_balance().
        """

        amount = self.normalize_amount(amount)

        if amount < 0:
            raise ValueError("Balance cannot be negative.")

        wallet = await self.get_or_create_wallet(user_id)

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
        Начислить деньги пользователю.

        Возвращает созданную финансовую транзакцию.

        Пример:

            await repository.add_balance(
                user_id=123,
                amount=10,
                transaction_type="reward",
                source="message",
            )
        """

        amount = self.normalize_amount(amount)

        if amount <= 0:
            raise ValueError(
                "add_balance amount must be greater than zero."
            )

        wallet = await self.get_or_create_wallet(user_id)

        balance_before = wallet.balance
        balance_after = balance_before + amount

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

        self.session.add(transaction)

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
        Списать деньги у пользователя.

        Если денег недостаточно — операция НЕ выполняется
        и возвращается None.
        """

        amount = self.normalize_amount(amount)

        if amount <= 0:
            raise ValueError(
                "remove_balance amount must be greater than zero."
            )

        wallet = await self.get_or_create_wallet(user_id)

        # Проверяем баланс.

        if wallet.balance < amount:
            return None

        balance_before = wallet.balance
        balance_after = balance_before - amount

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

        self.session.add(transaction)

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
        Перевести деньги между двумя пользователями.

        Возвращает:

            (transaction_sender, transaction_receiver)

        либо None, если у отправителя недостаточно средств.

        Сам commit() здесь НЕ выполняется.
        """

        amount = self.normalize_amount(amount)

        if amount <= 0:
            raise ValueError(
                "Transfer amount must be greater than zero."
            )

        if sender_id == receiver_id:
            raise ValueError(
                "Sender and receiver cannot be the same user."
            )

        # Получаем кошельки.

        sender_wallet = await self.get_or_create_wallet(sender_id)
        receiver_wallet = await self.get_or_create_wallet(receiver_id)

        # Проверяем средства.

        if sender_wallet.balance < amount:
            return None

        # ------------------------------------------------------------------
        # Sender
        # ------------------------------------------------------------------

        sender_before = sender_wallet.balance
        sender_after = sender_before - amount

        sender_wallet.balance = sender_after

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

        # ------------------------------------------------------------------
        # Receiver
        # ------------------------------------------------------------------

        receiver_before = receiver_wallet.balance
        receiver_after = receiver_before + amount

        receiver_wallet.balance = receiver_after

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
        """
        Получить количество гемов.
        """

        wallet = await self.get_wallet(user_id)

        if wallet is None:
            return 0

        return wallet.gems

    async def add_gems(
        self,
        *,
        user_id: int,
        amount: int,
    ) -> Wallet:
        """
        Начислить гемы.
        """

        if amount <= 0:
            raise ValueError(
                "Gem amount must be greater than zero."
            )

        wallet = await self.get_or_create_wallet(user_id)

        wallet.gems += amount

        await self.session.flush()

        return wallet

    async def remove_gems(
        self,
        *,
        user_id: int,
        amount: int,
    ) -> bool:
        """
        Списать гемы.

        Возвращает False при недостатке гемов.
        """

        if amount <= 0:
            raise ValueError(
                "Gem amount must be greater than zero."
            )

        wallet = await self.get_or_create_wallet(user_id)

        if wallet.gems < amount:
            return False

        wallet.gems -= amount

        await self.session.flush()

        return True

    # ========================================================================
    # TRANSACTIONS HISTORY
    # ========================================================================

    async def get_transactions(
        self,
        user_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Transaction]:
        """
        Получить историю финансовых операций пользователя.
        """

        if limit < 1:
            limit = 1

        if limit > 500:
            limit = 500

        if offset < 0:
            offset = 0

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
        """
        Получить конкретную транзакцию.
        """

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
        Административная корректировка баланса.

        amount > 0  -> начисление
        amount < 0  -> списание

        Нулевое изменение запрещено.
        """

        amount = self.normalize_amount(amount)

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