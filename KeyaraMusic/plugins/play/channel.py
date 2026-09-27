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
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus, ChatType
from pyrogram.types import Message

from KeyaraMusic import app
from KeyaraMusic.utils.database import set_cmode
from KeyaraMusic.utils.decorators.admins import AdminActual
from config import BANNED_USERS


@app.on_message(filters.command(["channelplay"]) & filters.group & ~BANNED_USERS)
@AdminActual
async def playmode_(client, message: Message, _):
    if len(message.command) < 2:
        return await message.reply_text(_["cplay_1"].format(message.chat.title))
    query = message.text.split(None, 2)[1].lower().strip()
    if (str(query)).lower() == "disable":
        await set_cmode(message.chat.id, None)
        return await message.reply_text(_["cplay_7"])
    elif str(query) == "linked":
        chat = await app.get_chat(message.chat.id)
        if chat.linked_chat:
            chat_id = chat.linked_chat.id
            await set_cmode(message.chat.id, chat_id)
            return await message.reply_text(
                _["cplay_3"].format(chat.linked_chat.title, chat.linked_chat.id)
            )
        else:
            return await message.reply_text(_["cplay_2"])
    else:
        try:
            chat = await app.get_chat(query)
        except:
            return await message.reply_text(_["cplay_4"])
        if chat.type != ChatType.CHANNEL:
            return await message.reply_text(_["cplay_5"])
        try:
            async for user in app.get_chat_members(
                chat.id, filter=ChatMembersFilter.ADMINISTRATORS
            ):
                if user.status == ChatMemberStatus.OWNER:
                    cusn = user.user.username
                    crid = user.user.id
        except:
            return await message.reply_text(_["cplay_4"])
        if crid != message.from_user.id:
            return await message.reply_text(_["cplay_6"].format(chat.title, cusn))
        await set_cmode(message.chat.id, chat.id)
        return await message.reply_text(_["cplay_3"].format(chat.title, chat.id))


# ©️ Copyright Reserved - @truenakshu  Saksham Swaroop

# ===========================================
# ©️ 2025 Saksham Swaroop (aka @truenakshu)
# 🔗 GitHub : https://github.com/VIP-saksham/KeyaraMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots 
