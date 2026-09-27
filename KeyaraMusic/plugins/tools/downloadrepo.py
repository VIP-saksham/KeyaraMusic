# =============================================================================
#  Copyright (c) 2026 Saksham Swaroop (@truenakshu)  |  GitHub: VIP-saksham
#  LinkedIn: sakshamswaroop
#
#  All rights reserved. This source code is the private property of the
#  author. Copying, modifying, redistributing or deploying any part of this
#  file WITHOUT the author's written permission is strictly prohibited.
#  For licensing / permission: https://t.me/truenakshu
# =============================================================================

import os
import shutil
import re
import tempfile
from urllib.parse import urlparse

import git
from pyrogram import filters

from KeyaraMusic import app
from KeyaraMusic.misc import SUDOERS


@app.on_message(filters.command(["downloadrepo"]) & SUDOERS)
def download_repo(_, message):
    if len(message.command) != 2:
        message.reply_text(
            "ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ɢɪᴛʜᴜʙ ʀᴇᴘᴏsɪᴛᴏʀʏ ᴜʀʟ ᴀғᴛᴇʀ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ. ᴇxᴀᴍᴘʟᴇ: /downloadrepo Repo Url "
        )
        return

    repo_url = message.command[1]
    zip_path = download_and_zip_repo(repo_url)

    if zip_path:
        with open(zip_path, "rb") as zip_file:
            message.reply_document(zip_file)
        os.remove(zip_path)
    else:
        message.reply_text("ᴜɴᴀʙʟᴇ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ᴛʜᴇ sᴘᴇᴄɪғɪᴇᴅ ɢɪᴛʜᴜʙ ʀᴇᴘᴏsɪᴛᴏʀʏ.")


def download_and_zip_repo(repo_url):
    repo_path = None
    try:
        parsed = urlparse(repo_url)
        if parsed.scheme != "https" or parsed.hostname != "github.com":
            raise ValueError("Only HTTPS GitHub repository URLs are allowed.")
        if not re.fullmatch(r"/[^/]+/[^/]+(?:\.git)?/?", parsed.path):
            raise ValueError("Invalid GitHub repository URL.")

        repo_name = os.path.basename(parsed.path.rstrip("/")).removesuffix(".git")
        repo_path = tempfile.mkdtemp(prefix="keyara-repo-")
        checkout_path = os.path.join(repo_path, repo_name)

        # Clone the repository
        git.Repo.clone_from(repo_url, checkout_path, depth=1)

        # Create a zip file of the repository
        zip_path = shutil.make_archive(repo_path, "zip", repo_path)

        return zip_path
    except Exception as e:
        print(f"ᴇʀʀᴏʀ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴀɴᴅ ᴢɪᴘᴘɪɴɢ ɢɪᴛʜᴜʙ ʀᴇᴘᴏsɪᴛᴏʀʏ: {e}")
        return None
    finally:
        if repo_path and os.path.exists(repo_path):
            shutil.rmtree(repo_path)


__MODULE__ = "Rᴇᴘᴏ"
__HELP__ = """
## Cᴏᴍᴍᴀɴᴅs Hᴇᴘ

### 1. /ᴅᴏᴡɴᴏᴀᴅʀᴇᴘᴏ
**Dᴇsᴄʀɪᴘᴛɪᴏɴ:**
Dᴏᴡɴᴏᴀᴅ ᴀɴᴅ ʀᴇᴛʀɪᴇᴠᴇ ғɪᴇs ғʀᴏᴍ ᴀ GɪᴛHᴜʙ ʀᴇᴘᴏsɪᴛᴏʀʏ.

**Usᴀɢᴇ:**
/ᴅᴏᴡɴᴏᴀᴅʀᴇᴘᴏ [Rᴇᴘᴏ_URL]

**Dᴇᴛᴀɪs:**
- Cᴏɴᴇs ᴛʜᴇ sᴘᴇᴄɪғɪᴇᴅ GɪᴛHᴜʙ ʀᴇᴘᴏsɪᴛᴏʀʏ.
- Cʀᴇᴀᴛᴇs ᴀ ᴢɪᴘ ғɪᴇ ᴏғ ᴛʜᴇ ʀᴇᴘᴏsɪᴛᴏʀʏ.
- Sᴇɴᴅs ᴛʜᴇ ᴢɪᴘ ғɪᴇ ʙᴀᴄᴋ ᴀs ᴀ ᴅᴏᴄᴜᴍᴇɴᴛ.
- Iғ ᴛʜᴇ ᴅᴏᴡɴᴏᴀᴅ ғᴀɪs, ᴀɴ ᴇʀʀᴏʀ ᴍᴇssᴀɢᴇ ᴡɪ ʙᴇ ᴅɪsᴘᴀʏᴇᴅ.

**Exᴀᴍᴘᴇs:**
- `/ᴅᴏᴡɴᴏᴀᴅʀᴇᴘᴏ ʜᴛᴛᴘs://ɢɪᴛʜᴜʙ.ᴄᴏᴍ/ᴜsᴇʀɴᴀᴍᴇ/ʀᴇᴘᴏsɪᴛᴏʀʏ`

"""


# ©️ Copyright Reserved - @truenakshu  Saksham Swaroop

# ===========================================
# ©️ 2025 Saksham Swaroop (aka @truenakshu)
# 🔗 GitHub : https://github.com/VIP-saksham/KeyaraMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots 
