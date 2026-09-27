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
from typing import List

import yaml

languages = {}
languages_present = {}

def _normalize_ui_text(value):
    if isinstance(value, str):
        return value.replace(
            "https://t.me/BlushMusicbot?start=help",
            "https://t.me/KeyaraMusicBot?start=help",
        )
    if isinstance(value, dict):
        return {key: _normalize_ui_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_ui_text(item) for item in value]
    return value


def get_string(lang: str):
    return languages[lang]


for filename in os.listdir(r"./strings/langs/"):
    if "en" not in languages:
        languages["en"] = _normalize_ui_text(yaml.safe_load(
            open(r"./strings/langs/en.yml", encoding="utf8")
        ))
        languages_present["en"] = languages["en"]["name"]
    if filename.endswith(".yml"):
        language_name = filename[:-4]
        if language_name == "en":
            continue
        languages[language_name] = _normalize_ui_text(yaml.safe_load(
            open(r"./strings/langs/" + filename, encoding="utf8")
        ))
        for item in languages["en"]:
            if item not in languages[language_name]:
                languages[language_name][item] = languages["en"][item]
    try:
        languages_present[language_name] = languages[language_name]["name"]
    except:
        print("There is some issue with the language file inside bot.")
        exit()


# ©️ Copyright Reserved - @truenakshu  Saksham Swaroop

# ===========================================
# ©️ 2025 Saksham Swaroop (aka @truenakshu)
# 🔗 GitHub : https://github.com/VIP-saksham/KeyaraMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots 
