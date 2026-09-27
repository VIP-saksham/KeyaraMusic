# =============================================================================
#  Copyright (c) 2026 Saksham Swaroop (@truenakshu)  |  GitHub: VIP-saksham
#  LinkedIn: sakshamswaroop
#
#  All rights reserved. This source code is the private property of the
#  author. Copying, modifying, redistributing or deploying any part of this
#  file WITHOUT the author's written permission is strictly prohibited.
#  For licensing / permission: https://t.me/truenakshu
# =============================================================================

from pyrogram.types import InlineKeyboardButton as Ikb

from .functions import get_urls_from_text as is_url


def keyboard(buttons_list, row_width: int = 2):
    row_width = max(1, min(int(row_width), 8))
    buttons = [
        (
            Ikb(text=str(i[0]), callback_data=str(i[1]))
            if not is_url(i[1])
            else Ikb(text=str(i[0]), url=str(i[1]))
        )
        for i in buttons_list
    ]
    return [
        buttons[i : i + row_width]
        for i in range(0, len(buttons), row_width)
    ]


def ikb(data: dict, row_width: int = 2):
    return keyboard(data.items(), row_width=row_width)


# ©️ Copyright Reserved - @truenakshu  Saksham Swaroop

# ===========================================
# ©️ 2025 Saksham Swaroop (aka @truenakshu)
# 🔗 GitHub : https://github.com/VIP-saksham/KeyaraMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots
