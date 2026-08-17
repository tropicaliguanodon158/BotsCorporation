from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.database.repositories.economy import EconomyRepository
from app.database.repositories.inventory import InventoryRepository
from app.services.inventory import InventoryService


router = Router(name="character_inventory")


def _service(session) -> InventoryService:
    return InventoryService(
        repository=InventoryRepository(session),
        economy_repository=EconomyRepository(session),
    )


@router.message(Command("inventory"))
async def inventory_handler(
    message: Message,
    session,
) -> None:
    if message.from_user is None:
        return

    service = _service(session)

    items = await service.get_inventory(
        user_id=message.from_user.id,
    )

    if not items:
        await message.answer(
            "🎒 <b>Инвентарь пуст.</b>"
        )
        return

    lines = ["🎒 <b>Твой инвентарь</b>\n"]

    for inventory_item in items:
        item = await service.get_item(
            inventory_item.item_id,
        )

        if item is None:
            continue

        display_name = (
            inventory_item.custom_name
            or item.name
        )

        lines.append(
            f"• <b>{display_name}</b> "
            f"×{inventory_item.quantity}\n"
            f"  ID: <code>{item.id}</code>\n"
            f"  Тип: {item.item_type}"
        )

    await message.answer(
        "\n\n".join(lines)
    )


@router.message(Command("item"))
async def item_handler(
    message: Message,
    command: CommandObject,
    session,
) -> None:
    args = (command.args or "").split()

    if len(args) != 1 or not args[0].isdigit():
        await message.answer(
            "Использование:\n"
            "<code>/item ID</code>"
        )
        return

    service = _service(session)

    item = await service.get_item(
        int(args[0]),
    )

    if item is None:
        await message.answer(
            "❌ Предмет не найден."
        )
        return

    await message.answer(
        "📦 <b>Предмет</b>\n\n"
        f"🆔 ID: <code>{item.id}</code>\n"
        f"📛 Название: <b>{item.name}</b>\n"
        f"📝 {item.description or 'Нет описания'}\n"
        f"🏷 Тип: {item.item_type}\n"
        f"💰 Цена: {item.price:.2f}\n"
        f"📦 Количество в инвентаре: "
        f"{await service.get_quantity(message.from_user.id, item.id) if message.from_user else 0}"
    )


@router.message(Command("use"))
async def use_handler(
    message: Message,
    command: CommandObject,
    session,
) -> None:
    if message.from_user is None:
        return

    args = (command.args or "").split()

    if len(args) != 1 or not args[0].isdigit():
        await message.answer(
            "Использование:\n"
            "<code>/use ID_предмета</code>"
        )
        return

    service = _service(session)

    try:
        item = await service.use_item(
            user_id=message.from_user.id,
            item_id=int(args[0]),
        )
    except (ValueError, RuntimeError) as exc:
        await message.answer(
            f"❌ {exc}"
        )
        return

    await message.answer(
        f"✅ Ты использовал предмет "
        f"<b>{item.name}</b>."
    )


@router.message(Command("equip"))
async def equip_handler(
    message: Message,
    command: CommandObject,
    session,
) -> None:
    if message.from_user is None:
        return

    args = (command.args or "").split()

    if len(args) != 1 or not args[0].isdigit():
        await message.answer(
            "Использование:\n"
            "<code>/equip ID_предмета</code>"
        )
        return

    service = _service(session)

    try:
        equipment = await service.equip_item(
            user_id=message.from_user.id,
            item_id=int(args[0]),
        )
    except (ValueError, RuntimeError) as exc:
        await message.answer(
            f"❌ {exc}"
        )
        return

    await message.answer(
        f"⚔️ Предмет <b>{equipment.item_id}</b> экипирован."
    )


@router.message(Command("unequip"))
async def unequip_handler(
    message: Message,
    command: CommandObject,
    session,
) -> None:
    if message.from_user is None:
        return

    args = (command.args or "").split()

    if len(args) != 1 or not args[0].isdigit():
        await message.answer(
            "Использование:\n"
            "<code>/unequip ID_предмета</code>"
        )
        return

    service = _service(session)

    try:
        success = await service.unequip_item(
            user_id=message.from_user.id,
            item_id=int(args[0]),
        )
    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )
        return

    if not success:
        await message.answer(
            "❌ Этот предмет не экипирован."
        )
        return

    await message.answer(
        "✅ Предмет снят."
    )


@router.message(Command("sell"))
async def sell_handler(
    message: Message,
    command: CommandObject,
    session,
) -> None:
    if message.from_user is None:
        return

    args = (command.args or "").split()

    if not args or not args[0].isdigit():
        await message.answer(
            "Использование:\n"
            "<code>/sell ID [количество]</code>"
        )
        return

    item_id = int(args[0])

    quantity = 1

    if len(args) >= 2:
        if not args[1].isdigit():
            await message.answer(
                "❌ Количество должно быть числом."
            )
            return

        quantity = int(args[1])

    service = _service(session)

    try:
        item, price = await service.sell_item(
            user_id=message.from_user.id,
            item_id=item_id,
            quantity=quantity,
        )
    except (ValueError, RuntimeError) as exc:
        await message.answer(
            f"❌ {exc}"
        )
        return

    await message.answer(
        "💰 <b>Продажа выполнена</b>\n\n"
        f"📦 {item.name} ×{quantity}\n"
        f"💵 Получено: <b>{price:.2f}</b>"
    )