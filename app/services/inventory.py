from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Sequence

from app.database.models.inventory import (
    Equipment,
    InventoryItem,
    Item,
)
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
    ) -> None:
        self.repository = repository

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
            raise ValueError(
                "Item does not exist."
            )

        if not item.is_active:
            raise ValueError(
                "Item is inactive."
            )

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

    async def get_item_price(
        self,
        item_id: int,
    ) -> Decimal:
        item = await self.repository.get_item(item_id)

        if item is None:
            raise ValueError(
                "Item does not exist."
            )

        return item.price

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
            raise ValueError(
                "Item does not exist."
            )

        if not item.is_active:
            raise ValueError(
                "Item is inactive."
            )

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
            raise ValueError(
                "Item does not exist."
            )

        if not item.is_sellable:
            raise ValueError(
                "This item cannot be sold."
            )

        return (
            item.price * quantity * rate
        ).quantize(Decimal("0.01"))

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
            raise ValueError(
                "Item does not exist."
            )

        if not item.is_active:
            raise ValueError(
                "Item is inactive."
            )

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
            raise ValueError(
                "Item does not exist."
            )

        if not item.is_active:
            raise ValueError(
                "Item is inactive."
            )

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