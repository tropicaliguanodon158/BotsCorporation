from __future__ import annotations

from aiogram import F, Router
from aiogram.types import ChatPermissions, Message

from app.database.repositories.moderation import ModerationRepository
from app.services.moderation import ModerationService


router = Router(name="moderation_filters")


@router.message(
    F.chat.type.in_(
        {
            "group",
            "supergroup",
        }
    ),
    F.text,
)
async def moderation_filter_handler(
    message: Message,
    session,
) -> None:
    if message.from_user is None:
        return

    if not message.text:
        return

    if message.text.startswith("/"):
        return

    service = ModerationService(
        ModerationRepository(session),
    )

    matched = await service.check_message(
        chat_id=message.chat.id,
        text=message.text,
    )

    if not matched:
        return

    for moderation_filter in matched:
        action = moderation_filter.action_type.lower()

        await service.record_action(
            moderator_id=None,
            target_user_id=message.from_user.id,
            chat_id=message.chat.id,
            action_type=(
                "delete_message"
                if action == "delete"
                else action
            ),
            reason=moderation_filter.reason,
            duration_seconds=(
                moderation_filter.duration_seconds
            ),
            metadata={
                "filter_id": moderation_filter.id,
                "pattern": moderation_filter.pattern,
            },
        )

        try:
            if action == "delete":
                await message.delete()

            elif action == "mute":
                await message.bot.restrict_chat_member(
                    chat_id=message.chat.id,
                    user_id=message.from_user.id,
                    permissions=ChatPermissions(
                        can_send_messages=False,
                    ),
                    until_date=(
                        moderation_filter.duration_seconds
                    ),
                )

            elif action == "ban":
                await message.bot.ban_chat_member(
                    chat_id=message.chat.id,
                    user_id=message.from_user.id,
                )

        except Exception:
            pass

        break