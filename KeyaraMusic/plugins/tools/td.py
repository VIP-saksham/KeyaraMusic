# =============================================================================
#  Copyright (c) 2026 Saksham Swaroop (@truenakshu)  |  GitHub: VIP-saksham
#  LinkedIn: sakshamswaroop
#
#  All rights reserved. This source code is the private property of the
#  author. Copying, modifying, redistributing or deploying any part of this
#  file WITHOUT the author's written permission is strictly prohibited.
#  For licensing / permission: https://t.me/truenakshu
# =============================================================================

import requests
from pyrogram import filters

from KeyaraMusic import app

truth_api_url = "https://api.truthordarebot.xyz/v1/truth"
dare_api_url = "https://api.truthordarebot.xyz/v1/dare"


@app.on_message(filters.command("truth"))
def get_truth(client, message):
    try:
        response = requests.get(truth_api_url)
        if response.status_code == 200:
            truth_question = response.json()["question"]
            message.reply_text(f"ᴛʀᴜᴛʜ ǫᴜᴇsᴛɪᴏɴ:\n\n{truth_question}")
        else:
            message.reply_text(
                "ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ ᴀ ᴛʀᴜᴛʜ ǫᴜᴇsᴛɪᴏɴ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."
            )
    except Exception as e:
        message.reply_text(
            "ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ғᴇᴛᴄʜɪɴɢ ᴀ ᴛʀᴜᴛʜ ǫᴜᴇsᴛɪᴏɴ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."
        )


@app.on_message(filters.command("dare"))
def get_dare(client, message):
    try:
        response = requests.get(dare_api_url)
        if response.status_code == 200:
            dare_question = response.json()["question"]
            message.reply_text(f"ᴅᴀʀᴇ ǫᴜᴇsᴛɪᴏɴ:\n\n{dare_question}")
        else:
            message.reply_text(
                "ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ ᴀ ᴅᴀʀᴇ ǫᴜᴇsᴛɪᴏɴ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."
            )
    except Exception as e:
        message.reply_text(
            "ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ғᴇᴛᴄʜɪɴɢ ᴀ ᴅᴀʀᴇ ǫᴜᴇsᴛɪᴏɴ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."
        )


__HELP__ = """
**ᴛʀᴜᴛʜ ᴏʀ ᴅᴀʀᴇ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs**

ᴜsᴇ ᴛʜᴇsᴇ ᴄᴏᴍᴍᴀɴᴅs ᴛᴏ ᴘʟᴀʏ ᴛʀᴜᴛʜ ᴏʀ ᴅᴀʀᴇ:

- `/truth`: ɢᴇᴛ ᴀ ʀᴀɴᴅᴏᴍ ᴛʀᴜᴛʜ ǫᴜᴇsᴛɪᴏɴ. ᴀɴsᴡᴇʀ ʜᴏɴᴇsᴛʟʏ!
- `/dare`: ɢᴇᴛ ᴀ ʀᴀɴᴅᴏᴍ ᴅᴀʀᴇ ᴄʜᴀʟʟᴇɴɢᴇ. ᴄᴏᴍᴘʟᴇᴛᴇ ɪᴛ ɪғ ʏᴏᴜ ᴅᴀʀᴇ!

**ᴇxᴀᴍᴘʟᴇs:**
- `/truth`: "ᴡʜᴀᴛ ɪs ʏᴏᴜʀ ᴍᴏsᴛ ᴇᴍʙᴀʀʀᴀssɪɴɢ ᴍᴏᴍᴇɴᴛ?"
- `/dare`: "ᴅᴏ 10 ᴘᴜsʜ-ᴜᴘs."

**ɴᴏᴛᴇ:**
ɪғ ʏᴏᴜ ᴇɴᴄᴏᴜɴᴛᴇʀ ᴀɴʏ ɪssᴜᴇs ᴡɪᴛʜ ғᴇᴛᴄʜɪɴɢ ǫᴜᴇsᴛɪᴏɴs, ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.
"""

__MODULE__ = "Tʀᴜᴛʜ"


# ©️ Copyright Reserved - @truenakshu  Saksham Swaroop

# ===========================================
# ©️ 2025 Saksham Swaroop (aka @truenakshu)
# 🔗 GitHub : https://github.com/VIP-saksham/KeyaraMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots 
