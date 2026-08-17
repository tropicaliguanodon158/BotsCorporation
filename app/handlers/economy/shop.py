from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.repositories.economy import EconomyRepository
from app.database.repositories.inventory import InventoryRepository
from app.services.inventory import InventoryService


router = Router(
    name="economy_shop",
)


@router.message(Command("shop"))
async def shop_handler(
    message: Message,
    session,
) -> None:
    """
    Показать активные товары магазина.
    """

    repository = InventoryRepository(session)
    service = InventoryService(repository)

    items = await service.get_active_items(
        limit=50,
    )

    if not items:
        await message.answer(
            "🛒 <b>Магазин пуст.</b>"
        )
        return

    lines = [
        "🛒 <b>Магазин</b>",
        "",
    ]

    for item in items:
        lines.append(
            f"<b>#{item.id}</b> — {item.name}\n"
            f"💰 {item.price:.2f}\n"
            f"📦 {item.item_type} | {item.rarity}"
        )

        if item.description:
            lines.append(
                f"└ {item.description}"
            )

        lines.append("")

    lines.append(
        "Купить: <code>/buy ID [количество]</code>\n"
        "Продать: <code>/sell ID [количество]</code>"
    )

    await message.answer(
        "\n".join(lines)
    )


@router.message(Command("buy"))
async def buy_handler(
    message: Message,
    session,
) -> None:
    """
    Купить предмет.

    /buy 1
    /buy 1 3
    """

    if message.from_user is None:
        return

    parts = (message.text or "").split()

    if len(parts) not in {2, 3}:
        await message.answer(
            "❌ Использование:\n"
            "<code>/buy ID [количество]</code>"
        )
        return

    try:
        item_id = int(parts[1])
        quantity = int(parts[2]) if len(parts) == 3 else 1
    except ValueError:
        await message.answer(
            "❌ ID и количество должны быть целыми числами."
        )
        return

    service = InventoryService(
        InventoryRepository(session),
        EconomyRepository(session),
    )

    try:
        item, total_price = await service.buy_item(
            user_id=message.from_user.id,
            item_id=item_id,
            quantity=quantity,
        )
    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )
        return

    await message.answer(
        "🛒 <b>Покупка совершена</b>\n\n"
        f"📦 {item.name} × {quantity}\n"
        f"💰 Списано: <b>{total_price:.2f}</b>"
    )


@router.message(Command("sell"))
async def sell_handler(
    message: Message,
    session,
) -> None:
    """
    Продать предмет.

    /sell 1
    /sell 1 3
    """

    if message.from_user is None:
        return

    parts = (message.text or "").split()

    if len(parts) not in {2, 3}:
        await message.answer(
            "❌ Использование:\n"
            "<code>/sell ID [количество]</code>"
        )
        return

    try:
        item_id = int(parts[1])
        quantity = int(parts[2]) if len(parts) == 3 else 1
    except ValueError:
        await message.answer(
            "❌ ID и количество должны быть целыми числами."
        )
        return

    service = InventoryService(
        InventoryRepository(session),
        EconomyRepository(session),
    )

    try:
        item, total_price = await service.sell_item(
            user_id=message.from_user.id,
            item_id=item_id,
            quantity=quantity,
        )
    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )
        return

    await message.answer(
        "💰 <b>Предмет продан</b>\n\n"
        f"📦 {item.name} × {quantity}\n"
        f"💵 Получено: <b>{total_price:.2f}</b>"
    )