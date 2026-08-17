from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Sequence

from app.database.models.inventory import (
    Equipment,
    InventoryItem,
    Item,
)
from app.database.repositories.economy import EconomyRepository
from app.database.repositories.inventory import InventoryRepository


class InventoryService:
    """
    Бизнес-логика инвентаря.

    Repository:
        только БД.

    Service:
        проверки;
        покупка/продажа;
        выдача;
        использование;
        экипировка;
        эффекты.
    """

    def __init__(
        self,
        repository: InventoryRepository,
        economy_repository: EconomyRepository | None = None,
    ) -> None:
        self.repository = repository
        self.economy = economy_repository

    # ========================================================================
    # ITEMS
    # ========================================================================

    async def get_item(
        self,
        item_id: int,
    ) -> Item | None:
        return await self.repository.get_item(item_id)

    async def get_active_items(
        self,
        *,
        item_type: str | None = None,
        rarity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Item]:
        return await self.repository.get_active_items(
            item_type=item_type,
            rarity=rarity,
            limit=limit,
            offset=offset,
        )

    # ========================================================================
    # INVENTORY
    # ========================================================================

    async def get_inventory(
        self,
        *,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[InventoryItem]:
        return await self.repository.get_inventory(
            user_id,
            limit=limit,
            offset=offset,
        )

    async def get_quantity(
        self,
        *,
        user_id: int,
        item_id: int,
    ) -> int:
        return await self.repository.get_quantity(
            user_id=user_id,
            item_id=item_id,
        )

    async def has_item(
        self,
        *,
        user_id: int,
        item_id: int,
        quantity: int = 1,
    ) -> bool:
        return await self.repository.has_item(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
        )

    async def give_item(
        self,
        *,
        user_id: int,
        item_id: int,
        quantity: int = 1,
        custom_name: str | None = None,
        custom_data: dict[str, Any] | None = None,
    ) -> InventoryItem:
        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        item = await self.repository.get_item(item_id)

        if item is None:
            raise ValueError("Item does not exist.")

        if not item.is_active:
            raise ValueError("Item is inactive.")

        custom_data_json = None

        if custom_data is not None:
            custom_data_json = json.dumps(
                custom_data,
                ensure_ascii=False,
                default=str,
            )

        return await self.repository.add_item(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
            custom_name=custom_name,
            custom_data=custom_data_json,
        )

    async def remove_item(
        self,
        *,
        user_id: int,
        item_id: int,
        quantity: int = 1,
    ) -> None:
        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        success = await self.repository.remove_item(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
        )

        if not success:
            raise ValueError(
                "User does not have enough of this item."
            )

    # ========================================================================
    # SHOP
    # ========================================================================

    async def calculate_buy_price(
        self,
        *,
        item_id: int,
        quantity: int,
    ) -> Decimal:
        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        item = await self.repository.get_item(item_id)

        if item is None:
            raise ValueError("Item does not exist.")

        if not item.is_active:
            raise ValueError("Item is inactive.")

        if item.price < 0:
            raise ValueError("Item has invalid price.")

        return (
            item.price * quantity
        ).quantize(Decimal("0.01"))

    async def calculate_sell_price(
        self,
        *,
        item_id: int,
        quantity: int,
        sell_rate: Decimal | int | float | str = Decimal("0.50"),
    ) -> Decimal:
        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        rate = Decimal(str(sell_rate))

        if rate < 0 or rate > 1:
            raise ValueError(
                "sell_rate must be between 0 and 1."
            )

        item = await self.repository.get_item(item_id)

        if item is None:
            raise ValueError("Item does not exist.")

        if not item.is_sellable:
            raise ValueError(
                "This item cannot be sold."
            )

        return (
            item.price * quantity * rate
        ).quantize(Decimal("0.01"))

    async def buy_item(
        self,
        *,
        user_id: int,
        item_id: int,
        quantity: int = 1,
    ) -> tuple[Item, Decimal]:
        """
        Купить предмет.

        Списание денег и выдача предмета выполняются
        в рамках одной транзакции middleware.
        """

        if self.economy is None:
            raise RuntimeError(
                "EconomyRepository is required for shop operations."
            )

        if user_id <= 0:
            raise ValueError("Invalid user_id.")

        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        item = await self.repository.get_item(item_id)

        if item is None:
            raise ValueError("Item does not exist.")

        if not item.is_active:
            raise ValueError("Item is inactive.")

        total_price = await self.calculate_buy_price(
            item_id=item_id,
            quantity=quantity,
        )

        transaction = await self.economy.remove_balance(
            user_id=user_id,
            amount=total_price,
            transaction_type="shop_purchase",
            source="shop",
            reference_id=f"item:{item_id}",
        )

        if transaction is None:
            raise ValueError(
                "Insufficient balance."
            )

        await self.repository.add_item(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
        )

        return item, total_price

    async def sell_item(
        self,
        *,
        user_id: int,
        item_id: int,
        quantity: int = 1,
        sell_rate: Decimal | int | float | str = Decimal("0.50"),
    ) -> tuple[Item, Decimal]:
        """
        Продать предмет.

        Сначала проверяется наличие предмета.
        После успешного списания предмета деньги начисляются
        в рамках той же транзакции.
        """

        if self.economy is None:
            raise RuntimeError(
                "EconomyRepository is required for shop operations."
            )

        if user_id <= 0:
            raise ValueError("Invalid user_id.")

        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        item = await self.repository.get_item(item_id)

        if item is None:
            raise ValueError("Item does not exist.")

        if not item.is_sellable:
            raise ValueError(
                "This item cannot be sold."
            )

        if not await self.repository.has_item(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
        ):
            raise ValueError(
                "You do not have enough of this item."
            )

        total_price = await self.calculate_sell_price(
            item_id=item_id,
            quantity=quantity,
            sell_rate=sell_rate,
        )

        success = await self.repository.remove_item(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
        )

        if not success:
            raise RuntimeError(
                "Inventory changed unexpectedly."
            )

        await self.economy.add_balance(
            user_id=user_id,
            amount=total_price,
            transaction_type="shop_sale",
            source="shop",
            reference_id=f"item:{item_id}",
        )

        return item, total_price

    # ========================================================================
    # USE
    # ========================================================================

    async def use_item(
        self,
        *,
        user_id: int,
        item_id: int,
        quantity: int = 1,
    ) -> Item:
        if quantity != 1:
            raise ValueError(
                "Item usage currently supports one item at a time."
            )

        item = await self.repository.get_item(item_id)

        if item is None:
            raise ValueError("Item does not exist.")

        if not item.is_active:
            raise ValueError("Item is inactive.")

        if not await self.repository.has_item(
            user_id=user_id,
            item_id=item_id,
            quantity=1,
        ):
            raise ValueError(
                "User does not own this item."
            )

        success = await self.repository.remove_item(
            user_id=user_id,
            item_id=item_id,
            quantity=1,
        )

        if not success:
            raise RuntimeError(
                "Inventory changed unexpectedly."
            )

        return item

    # ========================================================================
    # EQUIPMENT
    # ========================================================================

    async def get_equipment(
        self,
        user_id: int,
    ) -> Sequence[Equipment]:
        return await self.repository.get_equipment(user_id)

    async def equip_item(
        self,
        *,
        user_id: int,
        item_id: int,
    ) -> Equipment:
        item = await self.repository.get_item(item_id)

        if item is None:
            raise ValueError("Item does not exist.")

        if not item.is_active:
            raise ValueError("Item is inactive.")

        if item.item_type not in {
            "weapon",
            "armor",
            "equipment",
            "cosmetic",
        }:
            raise ValueError(
                "This item cannot be equipped."
            )

        if not await self.repository.has_item(
            user_id=user_id,
            item_id=item_id,
        ):
            raise ValueError(
                "User does not own this item."
            )

        return await self.repository.equip_item(
            user_id=user_id,
            item_id=item_id,
        )

    async def unequip_item(
        self,
        *,
        user_id: int,
        item_id: int,
    ) -> bool:
        return await self.repository.unequip_item(
            user_id=user_id,
            item_id=item_id,
        )

    # ========================================================================
    # ADMIN
    # ========================================================================

    async def set_quantity(
        self,
        *,
        user_id: int,
        item_id: int,
        quantity: int,
    ) -> InventoryItem:
        if quantity < 0:
            raise ValueError(
                "Quantity cannot be negative."
            )

        item = await self.repository.get_item(item_id)

        if item is None:
            raise ValueError(
                "Item does not exist."
            )

        return await self.repository.set_quantity(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
        )