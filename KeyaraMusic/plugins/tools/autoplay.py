# =============================================================================
#  Copyright (c) 2026 Saksham Swaroop (@truenakshu)  |  GitHub: VIP-saksham
#  LinkedIn: sakshamswaroop
#
#  All rights reserved. This source code is the private property of the
#  author. Copying, modifying, redistributing or deploying any part of this
#  file WITHOUT the author's written permission is strictly prohibited.
#  For licensing / permission: https://t.me/truenakshu
# =============================================================================

from pyrogram import filters
from pyrogram.types import Message

from KeyaraMusic import app
from KeyaraMusic.utils.database import autoplay_off, autoplay_on, get_lang, is_autoplay
from strings import get_string


@app.on_message(filters.command(["autoplay"]) & filters.group)
async def autoplay_toggle(client, message: Message):
    try:
        _ = get_string(await get_lang(message.chat.id))
    except Exception:
        _ = get_string("en")
    state = await is_autoplay(message.chat.id)
    new_state = not state
    if new_state:
        await autoplay_on(message.chat.id)
    else:
        await autoplay_off(message.chat.id)
    try:
        member = (
            await app.get_chat_member(message.chat.id, message.from_user.id)
        ).privileges
        can_manage = bool(member and member.can_manage_video_chats)
    except Exception:
        can_manage = False
    tip = (
        "\n\n<i>Sirf admins hi toggle kar sakein — ye status line hai.</i>"
        if not can_manage
        else ""
    )
    await message.reply_text(
        (_["autoplay_1"] if new_state else _["autoplay_2"]) + tip
    )


# Copyright (c) 2026 Saksham Swaroop - @truenakshu
