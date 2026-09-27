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

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait
from KeyaraMusic import app
from KeyaraMusic.utils.permissions import adminsOnly

chatQueue = []

stopProcess = False


@app.on_message(filters.command(["zombies"]))
@adminsOnly("can_restrict_members")
async def remove(client, message):

    global stopProcess
    try:
        try:
            sender = await app.get_chat_member(message.chat.id, message.from_user.id)
            has_permissions = sender.privileges
        except BaseException:
            has_permissions = message.sender_chat
        if has_permissions:
            bot = await app.get_chat_member(message.chat.id, "self")
            if bot.status == ChatMemberStatus.MEMBER:
                await message.reply(
                    "➠ | ɪ ɴᴇᴇᴅ ᴀᴅᴍɪɴ ᴘᴇʀᴍɪssɪᴏɴs ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs."
                )
            else:
                if len(chatQueue) > 30:
                    await message.reply(
                        "➠ | ɪ'ᴍ ᴀʟʀᴇᴀᴅʏ ᴡᴏʀᴋɪɴɢ ᴏɴ ᴍʏ ᴍᴀxɪᴍᴜᴍ ɴᴜᴍʙᴇʀ ᴏғ 30 ᴄʜᴀᴛs ᴀᴛ ᴛʜᴇ ᴍᴏᴍᴇɴᴛ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ sʜᴏʀᴛʟʏ."
                    )
                else:
                    if message.chat.id in chatQueue:
                        await message.reply(
                            "➠ | ᴛʜᴇʀᴇ's ᴀʟʀᴇᴀᴅʏ ᴀɴ ᴏɴɢɪɪɴɢ ᴘʀᴏᴄᴇss ɪɴ ᴛʜɪs ᴄʜᴀᴛ. ᴘʟᴇᴀsᴇ [ /stop ] ᴛᴏ sᴛᴀʀᴛ ᴀ ɴᴇᴡ ᴏɴᴇ."
                        )
                    else:
                        chatQueue.append(message.chat.id)
                        deletedList = []
                        async for member in app.get_chat_members(message.chat.id):
                            if member.user.is_deleted == True:
                                deletedList.append(member.user)
                            else:
                                pass
                        lenDeletedList = len(deletedList)
                        if lenDeletedList == 0:
                            await message.reply("⟳ | ɴᴏ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs ɪɴ ᴛʜɪs ᴄʜᴀᴛ.")
                            chatQueue.remove(message.chat.id)
                        else:
                            k = 0
                            processTime = lenDeletedList * 1
                            temp = await app.send_message(
                                message.chat.id,
                                f"🧭 | ᴛᴏᴛᴀʟ ᴏғ {lenDeletedList} ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs ʜᴀs ʙᴇᴇɴ ᴅᴇᴛᴇᴄᴛᴇᴅ.\n🥀 | ᴇsᴛɪᴍᴀᴛᴇᴅ ᴛɪᴍᴇ: {processTime} sᴇᴄᴏɴᴅs ғʀᴏᴍ ɴᴏᴡ.",
                            )
                            if stopProcess:
                                stopProcess = False
                            while len(deletedList) > 0 and not stopProcess:
                                deletedAccount = deletedList.pop(0)
                                try:
                                    await app.ban_chat_member(
                                        message.chat.id, deletedAccount.id
                                    )
                                except FloodWait as e:
                                    await asyncio.sleep(e.value)
                                except Exception:
                                    pass
                                k += 1
                            if k == lenDeletedList:
                                await message.reply(
                                    f"✅ | sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇᴍᴏᴠᴇᴅ ᴀʟʟ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄɪᴜɴᴛs ғʀᴏᴍ ᴛʜɪs ᴄʜᴀᴛ."
                                )
                                await temp.delete()
                            else:
                                await message.reply(
                                    f"✅ | sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇᴍᴏᴠᴇᴅ {k} ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs ғʀᴏᴍ ᴛʜɪs ᴄʜᴀᴛ."
                                )
                                await temp.delete()
                            chatQueue.remove(message.chat.id)
        else:
            await message.reply(
                "👮🏻 | sᴏʀʀʏ, **ᴏɴʟʏ ᴀᴅᴍɪɴ** ᴄᴀɴ ᴇxᴇᴄᴜᴛᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ."
            )
    except FloodWait as e:
        await asyncio.sleep(e.value)


__MODULE__ = "Zᴏᴍʙɪᴇs"
__HELP__ = """
**commands:**
- /zombies: ʀᴇᴍᴏᴠᴇ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs ғʀᴏᴍ ᴛʜᴇ ɢʀᴏᴜᴘ.

**info:**
- ᴍᴏᴅᴜʟᴇ ɴᴀᴍᴇ: ʀᴇᴍᴏᴠᴇ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs
- ᴅᴇsᴄʀɪᴘᴛɪᴏɴ: ʀᴇᴍᴏᴠᴇ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs ғʀᴏᴍ ᴛʜᴇ ɢʀᴏᴜᴘ.
- ᴄᴏᴍᴍᴀɴᴅs: /zombies
- ᴘᴇʀᴍɪssɪᴏɴs ɴᴇᴇᴅᴇᴅ: ᴄᴀɴ ʀᴇsᴛʀɪᴄᴛ ᴍᴇᴍʙᴇʀs

**note:**
- ᴜsᴇ ᴅɪʀᴇᴄᴛʟʏ ɪɴ ᴀ ɢʀᴏᴜᴘ ᴄʜᴀᴛ ᴡɪᴛʜ ᴍᴇ ғᴏʀ ʙᴇsᴛ ᴇғғᴇᴄᴛ. ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴇxᴇᴄᴜᴛᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ."""


# ©️ Copyright Reserved - @truenakshu  Saksham Swaroop

# ===========================================
# ©️ 2025 Saksham Swaroop (aka @truenakshu)
# 🔗 GitHub : https://github.com/VIP-saksham/KeyaraMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots 
