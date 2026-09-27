# =============================================================================
#  Copyright (c) 2026 Saksham Swaroop (@truenakshu)  |  GitHub: VIP-saksham
#  LinkedIn: sakshamswaroop
#
#  All rights reserved. This source code is the private property of the
#  author. Copying, modifying, redistributing or deploying any part of this
#  file WITHOUT the author's written permission is strictly prohibited.
#  For licensing / permission: https://t.me/truenakshu
# =============================================================================

import asyncio

from KeyaraMusic.misc import db
from KeyaraMusic.utils.database import get_active_chats, is_music_playing


async def timer():
    while not await asyncio.sleep(1):
        active_chats = await get_active_chats()
        for chat_id in active_chats:
            if not await is_music_playing(chat_id):
                continue
            playing = db.get(chat_id)
            if not playing:
                continue
            duration = int(playing[0]["seconds"])
            if duration == 0:
                continue
            if db[chat_id][0]["played"] >= duration:
                continue
            db[chat_id][0]["played"] += 1


asyncio.create_task(timer())


# ©️ Copyright Reserved - @truenakshu  Saksham Swaroop

# ===========================================
# ©️ 2025 Saksham Swaroop (aka @truenakshu)
# 🔗 GitHub : https://github.com/VIP-saksham/KeyaraMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots 
