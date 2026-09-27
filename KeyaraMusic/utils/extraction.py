# =============================================================================
#  Copyright (c) 2026 Saksham Swaroop (@truenakshu)  |  GitHub: VIP-saksham
#  LinkedIn: sakshamswaroop
#
#  All rights reserved. This source code is the private property of the
#  author. Copying, modifying, redistributing or deploying any part of this
#  file WITHOUT the author's written permission is strictly prohibited.
#  For licensing / permission: https://t.me/truenakshu
# =============================================================================

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, User

from KeyaraMusic import app


async def extract_user(m: Message) -> User:
    if m.reply_to_message:
        return m.reply_to_message.from_user
    msg_entities = m.entities[1] if m.text.startswith("/") else m.entities[0]
    return await app.get_users(
        msg_entities.user.id
        if msg_entities.type == MessageEntityType.TEXT_MENTION
        else int(m.command[1])
        if m.command[1].isdecimal()
        else m.command[1]
    )


# ©️ Copyright Reserved - @truenakshu  Saksham Swaroop

# ===========================================
# ©️ 2025 Saksham Swaroop (aka @truenakshu)
# 🔗 GitHub : https://github.com/VIP-saksham/KeyaraMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots 
