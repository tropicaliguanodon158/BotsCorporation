from __future__ import annotations

from decimal import Decimal
import random

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.interactions import InteractionType
from app.database.models.user import User
from app.database.models.economy import Wallet, Transaction
from app.services.media_pool import media_pool


router = Router(name="interactions")


# ============================================================================
# SIMPLE ENTERTAINMENT
# ============================================================================


@router.message(Command("coin"))
async def coin_handler(
    message: Message,
) -> None:
    result = random.choice(
        (
            "🪙 <b>Орёл!</b>",
            "🪙 <b>Решка!</b>",
        )
    )

    await message.answer(result)


@router.message(Command("8ball"))
async def eight_ball_handler(
    message: Message,
) -> None:
    answers = (
        "🎱 Без сомнений.",
        "🎱 Скорее всего.",
        "🎱 Возможно.",
        "🎱 Спроси позже.",
        "🎱 Сейчас я бы не рассчитывал.",
        "🎱 Определённо нет.",
        "🎱 Определённо да.",
    )

    await message.answer(
        random.choice(answers)
    )


@router.message(Command("choose"))
async def choose_handler(
    message: Message,
) -> None:
    text = (message.text or "").strip()

    parts = text.split(
        maxsplit=1
    )

    if len(parts) != 2:
        await message.answer(
            "🎯 <b>Использование</b>\n\n"
            "<code>/choose вариант1 | вариант2</code>"
        )
        return

    variants = [
        item.strip()
        for item in parts[1].split("|")
        if item.strip()
    ]

    if len(variants) < 2:
        await message.answer(
            "❌ Нужно указать минимум "
            "два варианта через <code>|</code>."
        )
        return

    await message.answer(
        "🎯 <b>Мой выбор:</b>\n\n"
        f"<b>{random.choice(variants)}</b>"
    )


@router.message(Command("roll"))
async def roll_handler(
    message: Message,
) -> None:
    text = (message.text or "").strip()

    parts = text.split(
        maxsplit=1
    )

    sides = 6

    if len(parts) == 2:
        value = parts[1].strip()

        if not value.isdigit():
            await message.answer(
                "❌ Количество граней должно быть числом."
            )
            return

        sides = int(value)

    if sides < 2 or sides > 1000:
        await message.answer(
            "❌ Количество граней должно быть "
            "от 2 до 1000."
        )
        return

    result = random.randint(
        1,
        sides,
    )

    await message.answer(
        f"🎲 <b>Бросок D{sides}</b>\n\n"
        f"🎯 Выпало: <b>{result}</b>"
    )


# ============================================================================
# TARGET RESOLUTION
# ============================================================================


async def _find_target(
    message: Message,
    session: AsyncSession,
) -> User | None:

    # ------------------------------------------------------------------------
    # Reply
    # ------------------------------------------------------------------------

    if message.reply_to_message is not None:
        telegram_user = (
            message.reply_to_message.from_user
        )

        if telegram_user is not None:
            result = await session.execute(
                select(User).where(
                    User.id == telegram_user.id
                )
            )

            return result.scalar_one_or_none()

    # ------------------------------------------------------------------------
    # @username / ID
    # ------------------------------------------------------------------------

    text = (
        message.text or ""
    ).strip()

    parts = text.split(
        maxsplit=1
    )

    if len(parts) != 2:
        return None

    target_value = parts[1].strip()

    if not target_value:
        return None

    target_value = target_value.split()[0]

    if target_value.startswith("@"):
        username = target_value[1:].lower()

        result = await session.execute(
            select(User).where(
                User.username.ilike(username)
            )
        )

        return result.scalar_one_or_none()

    try:
        target_id = int(target_value)
    except ValueError:
        return None

    result = await session.execute(
        select(User).where(
            User.id == target_id
        )
    )

    return result.scalar_one_or_none()


# ============================================================================
# BALANCE
# ============================================================================


async def _get_wallet(
    session: AsyncSession,
    user_id: int,
) -> Wallet | None:
    result = await session.execute(
        select(Wallet).where(
            Wallet.user_id == user_id
        )
    )

    return result.scalar_one_or_none()


async def _charge(
    session: AsyncSession,
    user_id: int,
    amount: Decimal,
) -> bool:
    if amount <= 0:
        return True

    wallet = await _get_wallet(
        session,
        user_id,
    )

    if wallet is None:
        return False

    if wallet.balance < amount:
        return False

    before = wallet.balance

    wallet.balance -= amount

    session.add(
        Transaction(
            user_id=user_id,
            amount=-amount,
            balance_before=before,
            balance_after=wallet.balance,
            transaction_type="interaction",
            source="interaction",
        )
    )

    await session.flush()

    return True


# ============================================================================
# RPG INTERACTIONS
# ============================================================================


@router.message(
    F.text.startswith("/")
)
async def interaction_command_handler(
    message: Message,
    session: AsyncSession,
) -> None:

    text = (
        message.text or ""
    ).strip()

    if not text.startswith("/"):
        return

    command_part = text.split(
        maxsplit=1
    )[0]

    command = command_part[1:]

    # Удаляем @botname:
    command = command.split(
        "@",
        1,
    )[0].lower()

    result = await session.execute(
        select(InteractionType).where(
            InteractionType.command == command,
            InteractionType.is_active.is_(True),
        )
    )

    interaction = (
        result.scalar_one_or_none()
    )

    if interaction is None:
        return

    if interaction.requires_target:
        target = await _find_target(
            message,
            session,
        )

        if target is None:
            await message.answer(
                "🎯 <b>Нужна цель</b>\n\n"
                "Используй команду ответом "
                "на сообщение пользователя или укажи "
                "<code>@username</code>."
            )
            return
    else:
        target = None

    actor = await session.get(
        User,
        message.from_user.id,
    )

    if actor is None:
        return

    if target is not None:
        if (
            target.id == actor.id
            and not interaction.allow_self_target
        ):
            await message.answer(
                "❌ Нельзя использовать это "
                "взаимодействие на себе."
            )
            return

    # ------------------------------------------------------------------------
    # Charge
    # ------------------------------------------------------------------------

    cost = Decimal(
        interaction.cost or 0
    )

    if not await _charge(
        session,
        actor.id,
        cost,
    ):
        await message.answer(
            "💸 <b>Недостаточно монет.</b>\n\n"
            f"Стоимость: <b>{cost}</b> 🪙"
        )
        return

    # ------------------------------------------------------------------------
    # Random result
    # ------------------------------------------------------------------------

    if interaction.has_random_result:
        roll = random.uniform(
            0,
            100,
        )

        if roll > float(
            interaction.success_chance
        ):
            result_text = (
                interaction.failure_text
                or "❌ Взаимодействие не удалось."
            )
        else:
            result_text = interaction.success_text

    else:
        result_text = interaction.success_text

    actor_name = (
        actor.first_name
        or actor.username
        or str(actor.id)
    )

    target_name = "-"

    if target is not None:
        target_name = (
            target.first_name
            or target.username
            or str(target.id)
        )

    result_text = result_text.format(
        actor=actor_name,
        target=target_name,
        amount=interaction.effect_value,
    )

    # ------------------------------------------------------------------------
    # Effect
    # ------------------------------------------------------------------------

    if (
        target is not None
        and interaction.effect_type == "damage"
        and interaction.effect_value > 0
    ):
        # Здесь намеренно не трогаем Character.
        #
        # Character combat будет отдельным сервисом,
        # чтобы взаимодействия не обходили RPG-логику.
        pass

    await session.flush()

    # ------------------------------------------------------------------------
    # Media
    # ------------------------------------------------------------------------

    image = media_pool.next(
        interaction.command
    )

    if image:
        await message.answer_photo(
            photo=image,
            caption=result_text,
        )
    else:
        await message.answer(
            result_text
        )