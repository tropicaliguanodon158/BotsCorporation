from __future__ import annotations

from datetime import timedelta

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.database.repositories.moderation import ModerationRepository
from app.services.moderation import ModerationService
from app.filters.admin import AdminFilter


router = Router(name="moderation")


def _service(session) -> ModerationService:
    return ModerationService(
        ModerationRepository(session),
    )


def _target_user(message: Message) -> int | None:
    if message.reply_to_message is None:
        return None

    if message.reply_to_message.from_user is None:
        return None

    return message.reply_to_message.from_user.id


async def _moderation_action(
    message: Message,
    session,
    action: str,
    duration: int | None = None,
) -> None:
    if message.from_user is None:
        return

    if message.chat.type not in {
        "group",
        "supergroup",
    }:
        await message.answer(
            "❌ Команда доступна только в группах."
        )
        return

    target_id = _target_user(message)

    if target_id is None:
        await message.answer(
            "❌ Используй команду ответом на сообщение пользователя."
        )
        return

    if target_id == message.from_user.id:
        await message.answer(
            "❌ Нельзя применить действие к себе."
        )
        return

    reason = None

    if message.text:
        parts = message.text.split(maxsplit=2)

        if len(parts) >= 2:
            reason = parts[-1]

    service = _service(session)

    try:
        await service.record_action(
            moderator_id=message.from_user.id,
            target_user_id=target_id,
            chat_id=message.chat.id,
            action_type=action,
            reason=reason,
            duration_seconds=duration,
        )
    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )
        return

    try:
        if action == "kick":
            await message.bot.ban_chat_member(
                chat_id=message.chat.id,
                user_id=target_id,
            )
            await message.bot.unban_chat_member(
                chat_id=message.chat.id,
                user_id=target_id,
            )

        elif action == "ban":
            await message.bot.ban_chat_member(
                chat_id=message.chat.id,
                user_id=target_id,
            )

        elif action == "mute":
            permissions = {
                "can_send_messages": False,
                "can_send_audios": False,
                "can_send_documents": False,
                "can_send_photos": False,
                "can_send_videos": False,
                "can_send_video_notes": False,
                "can_send_voice_notes": False,
                "can_send_polls": False,
                "can_send_other_messages": False,
                "can_add_web_page_previews": False,
                "can_change_info": False,
                "can_invite_users": False,
                "can_pin_messages": False,
                "can_manage_topics": False,
            }

            from aiogram.types import ChatPermissions

            await message.bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=target_id,
                permissions=ChatPermissions(
                    **permissions,
                ),
                until_date=(
                    timedelta(seconds=duration)
                    if duration
                    else None
                ),
            )

        elif action == "unmute":
            from aiogram.types import ChatPermissions

            await message.bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=target_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_audios=True,
                    can_send_documents=True,
                    can_send_photos=True,
                    can_send_videos=True,
                    can_send_video_notes=True,
                    can_send_voice_notes=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                    can_manage_topics=True,
                ),
            )

        elif action == "delete_message":
            await message.delete()

    except Exception:
        await message.answer(
            "⚠️ Действие записано в БД, "
            "но Telegram не позволил выполнить операцию."
        )
        return

    await message.answer(
        f"✅ Действие <b>{action}</b> применено."
    )


@router.message(
    Command("warn"),
    AdminFilter(required_level=2),
)
async def warn_handler(
    message: Message,
    session,
) -> None:
    if message.from_user is None:
        return

    target_id = _target_user(message)

    if target_id is None:
        await message.answer(
            "❌ Используй /warn ответом на сообщение."
        )
        return

    reason = None

    if message.text:
        parts = message.text.split(maxsplit=1)

        if len(parts) == 2:
            reason = parts[1]

    service = _service(session)

    try:
        warning = await service.warn(
            moderator_id=message.from_user.id,
            target_user_id=target_id,
            chat_id=message.chat.id,
            reason=reason,
        )
    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )
        return

    count = await service.get_warning_count(
        user_id=target_id,
        chat_id=message.chat.id,
    )

    await message.answer(
        "⚠️ <b>Предупреждение выдано.</b>\n\n"
        f"ID предупреждения: <code>{warning.id}</code>\n"
        f"Активных предупреждений: <b>{count}</b>"
    )


@router.message(
    Command("mute"),
    AdminFilter(required_level=2),
)
async def mute_handler(
    message: Message,
    command: CommandObject,
    session,
) -> None:
    duration = 3600

    if command.args:
        value = command.args.split()[0]

        if value.isdigit():
            duration = int(value) * 60

    await _moderation_action(
        message=message,
        session=session,
        action="mute",
        duration=duration,
    )


@router.message(
    Command("ban"),
    AdminFilter(required_level=3),
)
async def ban_handler(
    message: Message,
    session,
) -> None:
    await _moderation_action(
        message=message,
        session=session,
        action="ban",
    )


@router.message(
    Command("kick"),
    AdminFilter(required_level=2),
)
async def kick_handler(
    message: Message,
    session,
) -> None:
    await _moderation_action(
        message=message,
        session=session,
        action="kick",
    )


@router.message(
    Command("unmute"),
    AdminFilter(required_level=2),
)
async def unmute_handler(
    message: Message,
    session,
) -> None:
    await _moderation_action(
        message=message,
        session=session,
        action="unmute",
    )


@router.message(
    Command("unwarn"),
    AdminFilter(required_level=2),
)
async def unwarn_handler(
    message: Message,
    session,
) -> None:
    if message.from_user is None:
        return

    target_id = _target_user(message)

    if target_id is None:
        await message.answer(
            "❌ Используй /unwarn ответом на сообщение."
        )
        return

    service = _service(session)

    try:
        count = await service.clear_warnings(
            moderator_id=message.from_user.id,
            target_user_id=target_id,
            chat_id=message.chat.id,
        )
    except ValueError as exc:
        await message.answer(
            f"❌ {exc}"
        )
        return

    await message.answer(
        f"✅ Снято предупреждений: <b>{count}</b>."
    )