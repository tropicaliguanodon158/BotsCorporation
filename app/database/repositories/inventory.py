"""
Repository for inventory and equipment.

Отвечает за:
    - игровые предметы;
    - инвентарь пользователей;
    - экипировку;
    - количество предметов;
    - создание и настройку предметов.

Бизнес-логика магазина, кейсов, использования предметов
и эффектов находится в services.
"""

from decimal import Decimal
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.inventory import (
    Equipment,
    InventoryItem,
    Item,
)


class InventoryRepository:
    """
    Репозиторий предметов, инвентаря и экипировки.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ========================================================================
    # ITEMS
    # ========================================================================

    async def get_item(
        self,
        item_id: int,
    ) -> Item | None:
        """
        Получить предмет по ID.
        """

        result = await self.session.execute(
            select(Item).where(
                Item.id == item_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_item_by_name(
        self,
        name: str,
    ) -> Item | None:
        """
        Получить предмет по названию без учёта регистра.
        """

        name = name.strip()

        if not name:
            return None

        result = await self.session.execute(
            select(Item).where(
                Item.name.ilike(name),
            )
        )

        return result.scalar_one_or_none()

    async def get_active_items(
        self,
        *,
        item_type: str | None = None,
        rarity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Item]:
        """
        Получить активные предметы.

        Можно фильтровать:
            - по типу;
            - по редкости.
        """

        limit = max(1, min(limit, 1000))
        offset = max(0, offset)

        query = select(Item).where(
            Item.is_active.is_(True),
        )

        if item_type is not None:
            query = query.where(
                Item.item_type == item_type,
            )

        if rarity is not None:
            query = query.where(
                Item.rarity == rarity,
            )

        query = (
            query
            .order_by(Item.id)
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    async def create_item(
        self,
        *,
        name: str,
        description: str = "",
        item_type: str,
        rarity: str = "common",
        price: Decimal | int | float | str = Decimal("0.00"),
        hp_bonus: int = 0,
        strength_bonus: int = 0,
        defense_bonus: int = 0,
        luck_bonus: int = 0,
        speed_bonus: int = 0,
        intelligence_bonus: int = 0,
        effect_type: str | None = None,
        effect_value: int = 0,
        effect_duration_seconds: int = 0,
        is_tradeable: bool = True,
        is_sellable: bool = True,
        is_active: bool = True,
    ) -> Item:
        """
        Создать новый игровой предмет.
        """

        price = Decimal(str(price)).quantize(
            Decimal("0.01")
        )

        if price < 0:
            raise ValueError(
                "Item price cannot be negative."
            )

        item = Item(
            name=name.strip(),
            description=description,
            item_type=item_type,
            rarity=rarity,
            price=price,
            hp_bonus=hp_bonus,
            strength_bonus=strength_bonus,
            defense_bonus=defense_bonus,
            luck_bonus=luck_bonus,
            speed_bonus=speed_bonus,
            intelligence_bonus=intelligence_bonus,
            effect_type=effect_type,
            effect_value=effect_value,
            effect_duration_seconds=max(
                0,
                effect_duration_seconds,
            ),
            is_tradeable=is_tradeable,
            is_sellable=is_sellable,
            is_active=is_active,
        )

        self.session.add(item)

        await self.session.flush()

        return item

    async def update_item(
        self,
        item_id: int,
        **values: object,
    ) -> Item | None:
        """
        Изменить параметры предмета.

        Именно этот метод впоследствии будет использовать
        Founder Panel.
        """

        allowed_fields = {
            "name",
            "description",
            "item_type",
            "rarity",
            "price",
            "hp_bonus",
            "strength_bonus",
            "defense_bonus",
            "luck_bonus",
            "speed_bonus",
            "intelligence_bonus",
            "effect_type",
            "effect_value",
            "effect_duration_seconds",
            "is_tradeable",
            "is_sellable",
            "is_active",
        }

        invalid_fields = set(values) - allowed_fields

        if invalid_fields:
            raise ValueError(
                "Unsupported item fields: "
                + ", ".join(sorted(invalid_fields))
            )

        item = await self.get_item(item_id)

        if item is None:
            return None

        if "price" in values:
            price = Decimal(
                str(values["price"])
            ).quantize(Decimal("0.01"))

            if price < 0:
                raise ValueError(
                    "Item price cannot be negative."
                )

            values["price"] = price

        for field, value in values.items():
            setattr(item, field, value)

        await self.session.flush()

        return item

    # ========================================================================
    # INVENTORY
    # ========================================================================

    async def get_inventory_item(
        self,
        *,
        user_id: int,
        item_id: int,
    ) -> InventoryItem | None:
        """
        Получить конкретный предмет из инвентаря пользователя.
        """

        result = await self.session.execute(
            select(InventoryItem).where(
                InventoryItem.user_id == user_id,
                InventoryItem.item_id == item_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_inventory(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[InventoryItem]:
        """
        Получить инвентарь пользователя.
        """

        limit = max(1, min(limit, 1000))
        offset = max(0, offset)

        result = await self.session.execute(
            select(InventoryItem)
            .where(
                InventoryItem.user_id == user_id,
                InventoryItem.quantity > 0,
            )
            .order_by(
                InventoryItem.id,
            )
            .offset(offset)
            .limit(limit)
        )

        return result.scalars().all()

    async def get_quantity(
        self,
        *,
        user_id: int,
        item_id: int,
    ) -> int:
        """
        Получить количество предмета.

        Если предмет отсутствует — 0.
        """

        inventory_item = await self.get_inventory_item(
            user_id=user_id,
            item_id=item_id,
        )

        if inventory_item is None:
            return 0

        return inventory_item.quantity

    async def has_item(
        self,
        *,
        user_id: int,
        item_id: int,
        quantity: int = 1,
    ) -> bool:
        """
        Проверить наличие предмета в указанном количестве.
        """

        if quantity <= 0:
            return True

        current_quantity = await self.get_quantity(
            user_id=user_id,
            item_id=item_id,
        )

        return current_quantity >= quantity

    # ========================================================================
    # ADD ITEMS
    # ========================================================================

    async def add_item(
        self,
        *,
        user_id: int,
        item_id: int,
        quantity: int = 1,
        custom_name: str | None = None,
        custom_data: str | None = None,
    ) -> InventoryItem:
        """
        Добавить предмет пользователю.

        Если предмет уже есть:
            quantity увеличивается.

        Если предмета нет:
            создаётся новая запись.
        """

        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        inventory_item = await self.get_inventory_item(
            user_id=user_id,
            item_id=item_id,
        )

        if inventory_item is None:
            inventory_item = InventoryItem(
                user_id=user_id,
                item_id=item_id,
                quantity=quantity,
                custom_name=custom_name,
                custom_data=custom_data,
            )

            self.session.add(inventory_item)

        else:
            inventory_item.quantity += quantity

            if custom_name is not None:
                inventory_item.custom_name = custom_name

            if custom_data is not None:
                inventory_item.custom_data = custom_data

        await self.session.flush()

        return inventory_item

    async def add_items(
        self,
        *,
        user_id: int,
        items: dict[int, int],
    ) -> list[InventoryItem]:
        """
        Массово добавить предметы.
        """

        result: list[InventoryItem] = []

        for item_id, quantity in items.items():

            if quantity <= 0:
                continue

            inventory_item = await self.add_item(
                user_id=user_id,
                item_id=item_id,
                quantity=quantity,
            )

            result.append(inventory_item)

        return result

    # ========================================================================
    # REMOVE ITEMS
    # ========================================================================

    async def remove_item(
        self,
        *,
        user_id: int,
        item_id: int,
        quantity: int = 1,
    ) -> bool:
        """
        Списать предмет.

        False:
            предмета недостаточно.

        True:
            предмет успешно списан.
        """

        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        inventory_item = await self.get_inventory_item(
            user_id=user_id,
            item_id=item_id,
        )

        if inventory_item is None:
            return False

        if inventory_item.quantity < quantity:
            return False

        inventory_item.quantity -= quantity

        await self.session.flush()

        return True

    async def remove_items(
        self,
        *,
        user_id: int,
        items: dict[int, int],
    ) -> bool:
        """
        Массовое списание предметов.

        Сначала проверяются ВСЕ предметы.
        Только после успешной проверки происходит списание.
        """

        # ------------------------------------------------------------------
        # Проверяем всё заранее.
        # ------------------------------------------------------------------

        for item_id, quantity in items.items():

            if quantity <= 0:
                raise ValueError(
                    "Quantity must be greater than zero."
                )

            if not await self.has_item(
                user_id=user_id,
                item_id=item_id,
                quantity=quantity,
            ):
                return False

        # ------------------------------------------------------------------
        # Списываем.
        # ------------------------------------------------------------------

        for item_id, quantity in items.items():

            success = await self.remove_item(
                user_id=user_id,
                item_id=item_id,
                quantity=quantity,
            )

            if not success:
                raise RuntimeError(
                    "Inventory changed unexpectedly "
                    "during mass removal."
                )

        return True

    # ========================================================================
    # SET QUANTITY
    # ========================================================================

    async def set_quantity(
        self,
        *,
        user_id: int,
        item_id: int,
        quantity: int,
    ) -> InventoryItem:
        """
        Установить количество предмета.

        Используется Founder Panel и административными
        сервисами.
        """

        if quantity < 0:
            raise ValueError(
                "Quantity cannot be negative."
            )

        inventory_item = await self.get_inventory_item(
            user_id=user_id,
            item_id=item_id,
        )

        if inventory_item is None:

            inventory_item = InventoryItem(
                user_id=user_id,
                item_id=item_id,
                quantity=quantity,
            )

            self.session.add(inventory_item)

        else:
            inventory_item.quantity = quantity

        await self.session.flush()

        return inventory_item

    # ========================================================================
    # CUSTOMIZATION
    # ========================================================================

    async def update_inventory_item(
        self,
        *,
        user_id: int,
        item_id: int,
        custom_name: str | None = None,
        custom_data: str | None = None,
    ) -> InventoryItem | None:
        """
        Изменить пользовательские данные конкретного предмета.
        """

        inventory_item = await self.get_inventory_item(
            user_id=user_id,
            item_id=item_id,
        )

        if inventory_item is None:
            return None

        if custom_name is not None:
            inventory_item.custom_name = custom_name

        if custom_data is not None:
            inventory_item.custom_data = custom_data

        await self.session.flush()

        return inventory_item

    # ========================================================================
    # CLEAR
    # ========================================================================

    async def clear_item(
        self,
        *,
        user_id: int,
        item_id: int,
    ) -> bool:
        """
        Полностью удалить предмет из инвентаря.
        """

        inventory_item = await self.get_inventory_item(
            user_id=user_id,
            item_id=item_id,
        )

        if inventory_item is None:
            return False

        await self.session.delete(inventory_item)

        await self.session.flush()

        return True

    async def clear_inventory(
        self,
        user_id: int,
    ) -> int:
        """
        Полностью очистить инвентарь пользователя.

        Возвращает количество удалённых записей.
        """

        items = await self.get_inventory(
            user_id,
            limit=1000,
        )

        count = 0

        for inventory_item in items:
            await self.session.delete(inventory_item)
            count += 1

        await self.session.flush()

        return count

    # ========================================================================
    # EQUIPMENT
    # ========================================================================

    async def get_equipment(
        self,
        user_id: int,
    ) -> Sequence[Equipment]:
        """
        Получить всю экипировку пользователя.
        """

        result = await self.session.execute(
            select(Equipment)
            .where(
                Equipment.user_id == user_id,
            )
            .order_by(
                Equipment.slot,
            )
        )

        return result.scalars().all()

    async def get_equipped_item(
        self,
        *,
        user_id: int,
        slot: str,
    ) -> Equipment | None:
        """
        Получить предмет, экипированный в конкретный слот.
        """

        result = await self.session.execute(
            select(Equipment).where(
                Equipment.user_id == user_id,
                Equipment.slot == slot,
            )
        )

        return result.scalar_one_or_none()

    async def get_equipment_by_item(
        self,
        *,
        user_id: int,
        item_id: int,
    ) -> Equipment | None:
        """
        Проверить, экипирован ли конкретный предмет.
        """

        result = await self.session.execute(
            select(Equipment).where(
                Equipment.user_id == user_id,
                Equipment.item_id == item_id,
            )
        )

        return result.scalar_one_or_none()

    async def equip_item(
        self,
        *,
        user_id: int,
        item_id: int,
        slot: str,
    ) -> Equipment:
        """
        Экипировать предмет.

        Если слот уже занят, существующая экипировка
        заменяется.

        Проверку наличия предмета в инвентаре выполняет
        Character/Inventory Service.
        """

        slot = slot.strip()

        if not slot:
            raise ValueError(
                "Equipment slot cannot be empty."
            )

        equipment = await self.get_equipped_item(
            user_id=user_id,
            slot=slot,
        )

        if equipment is None:

            equipment = Equipment(
                user_id=user_id,
                item_id=item_id,
                slot=slot,
            )

            self.session.add(equipment)

        else:
            equipment.item_id = item_id

        await self.session.flush()

        return equipment

    async def unequip_item(
        self,
        *,
        user_id: int,
        slot: str,
    ) -> bool:
        """
        Снять предмет из слота.
        """

        equipment = await self.get_equipped_item(
            user_id=user_id,
            slot=slot,
        )

        if equipment is None:
            return False

        await self.session.delete(equipment)

        await self.session.flush()

        return True

    async def unequip_item_by_id(
        self,
        *,
        user_id: int,
        item_id: int,
    ) -> bool:
        """
        Снять конкретный экипированный предмет.
        """

        equipment = await self.get_equipment_by_item(
            user_id=user_id,
            item_id=item_id,
        )

        if equipment is None:
            return False

        await self.session.delete(equipment)

        await self.session.flush()

        return True