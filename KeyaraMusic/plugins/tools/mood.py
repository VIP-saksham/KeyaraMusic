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
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from pytgcalls.exceptions import NoActiveGroupCall

from KeyaraMusic import YouTube, app
from KeyaraMusic.core.call import Nand
from KeyaraMusic.misc import db
from KeyaraMusic.utils.database import get_lang, is_active_chat
from KeyaraMusic.utils.inline.play import stream_markup
from KeyaraMusic.utils.stream.autoplay import (
    MOOD_EMOJIS,
    _add_to_queue,
    pick_mood_tracks,
)
from strings import get_string

MOODS = ["happy", "sad", "romantic", "energy", "chill", "focus", "party", "sleep"]


def mood_markup():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("😊 Happy", callback_data="mood|happy"),
                InlineKeyboardButton("🥺 Sad", callback_data="mood|sad"),
            ],
            [
                InlineKeyboardButton("💕 Romantic", callback_data="mood|romantic"),
                InlineKeyboardButton("🔥 Energy", callback_data="mood|energy"),
            ],
            [
                InlineKeyboardButton("😌 Chill", callback_data="mood|chill"),
                InlineKeyboardButton("🎧 Focus", callback_data="mood|focus"),
            ],
            [
                InlineKeyboardButton("🎉 Party", callback_data="mood|party"),
                InlineKeyboardButton("🌙 Sleep", callback_data="mood|sleep"),
            ],
        ]
    )


@app.on_message(filters.command(["mood"]) & filters.group)
async def mood_command(client, message: Message):
    try:
        _ = get_string(await get_lang(message.chat.id))
    except Exception:
        _ = get_string("en")
    await message.reply_text(_["mood_1"], reply_markup=mood_markup())


@app.on_callback_query(filters.regex(r"^mood\|"))
async def mood_pick(client, cb: CallbackQuery):
    mood = cb.data.split("|", 1)[1].strip().lower()
    if mood not in MOODS:
        return await cb.answer("Unknown mood!", show_alert=True)
    chat_id = cb.message.chat.id
    user = cb.from_user.first_name or "Someone"
    user_id = cb.from_user.id
    await cb.answer("🎵 " + mood.title() + " mood selected!", show_alert=False)
    try:
        _ = get_string(await get_lang(chat_id))
    except Exception:
        _ = get_string("en")

    status = await cb.message.reply_text(_["mood_2"].format(mood.title()))
    try:
        tracks = await pick_mood_tracks(mood, limit=4)
    except Exception as e:
        return await status.edit_text(
            _["mood_4"] + f"\n\n<code>{type(e).__name__}</code>"
        )
    if not tracks:
        return await status.edit_text(_["mood_4"])

    if not await is_active_chat(chat_id):
        db[chat_id] = []  # stale entries clear before fresh mood queue
    for t in tracks:
        _add_to_queue(chat_id, t, user, user_id)

    if not await is_active_chat(chat_id):
        first = tracks[0]
        mystic = await status.edit_text(_["call_4"].format(app.mention))
        try:
            file_path, direct = await YouTube.download(
                first["vidid"], mystic, videoid=True, video=None
            )
            if not file_path:
                raise RuntimeError("no stream url")
            await Nand.join_call(
                chat_id,
                chat_id,
                file_path,
                video=None,
                image=first.get("thumb") or "",
            )
            run = await mystic.edit(
                _["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{first['vidid']}",
                    first["title"][:23],
                    first.get("duration_min") or "0:00",
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(stream_markup(_, chat_id)),
                disable_web_page_preview=True,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
        except NoActiveGroupCall:
            try:
                await mystic.edit_text(_["call_1"])
            except Exception:
                pass
        except Exception:
            try:
                await mystic.edit_text(_["call_10"])
            except Exception:
                pass

    q = db.get(chat_id) or []
    lines = "\n".join(
        f"{i + 1}. {item['title'][:42]}" for i, item in enumerate(q[:4])
    )
    try:
        await status.edit_text(
            _["mood_3"].format(
                MOOD_EMOJIS.get(mood, "🎵"), mood.title(), lines, len(q)
            ),
            disable_web_page_preview=True,
        )
    except Exception:
        pass


# Copyright (c) 2026 Saksham Swaroop - @truenakshu
