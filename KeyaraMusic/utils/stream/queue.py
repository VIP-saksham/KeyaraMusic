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
from typing import Union

from KeyaraMusic.misc import db
from KeyaraMusic.utils.formatters import check_duration, seconds_to_min
from config import autoclean, time_to_seconds

# --- next-song precache: queue add hote hi BG download/warm (super fast) ---
_PRECACHE_SEM = asyncio.Semaphore(2)
_precache_seen = set()


async def _precache_api(vidid, kind):
    """API cache warm — /api/stream extract+archive BG me kar deta hai,
    isliye turn aane tak video/audio URL instant milta hai."""
    try:
        import aiohttp
        from KeyaraMusic.platforms.Youtube import API_URL as _au
        from KeyaraMusic.platforms.Youtube import API_KEY as _ak
        vid = str(vidid or '').strip()
        if not _au or not _ak or len(vid) != 11:
            return
        to = aiohttp.ClientTimeout(total=150, connect=10)
        async with aiohttp.ClientSession(timeout=to) as _ses:
            async with _ses.get(
                f'{_au}/api/stream',
                params={
                    'url': f'https://www.youtube.com/watch?v={vid}',
                    'type': kind,
                    'api_key': _ak,
                },
            ) as _r:
                await _r.read()
    except Exception:
        pass


async def _precache_download(title, vidid, is_video=False):
    if is_video:
        await _precache_api(vidid, 'video')
        return
    q = str(title or vidid or '').strip()
    if not q:
        return
    try:
        from KeyaraMusic.core.call import Nand as _tg_Nand
        from KeyaraMusic.utils.tgsongs import (
            download_song as _tg_dl,
            get_cached as _tg_cached,
        )
        client = getattr(_tg_Nand, 'userbot1', None)
        if not client or await _tg_cached(q):
            return
        got = await asyncio.wait_for(_tg_dl(client, q), timeout=180)
        if not got:
            await _precache_api(vidid, 'audio')
    except Exception:
        pass


def _spawn_precache(title, vidid, is_video=False):
    q = str(title or vidid or '').strip().lower()
    if not q or q in _precache_seen:
        return
    if len(_precache_seen) > 2000:
        _precache_seen.clear()
    _precache_seen.add(q)
    try:
        asyncio.get_running_loop().create_task(
            _precache_download(title, vidid, bool(is_video))
        )
    except Exception:
        pass



async def put_queue(
    chat_id,
    original_chat_id,
    file,
    title,
    duration,
    user,
    vidid,
    user_id,
    stream,
    forceplay: Union[bool, str] = None,
):
    title = title.title()
    try:
        duration_in_seconds = time_to_seconds(duration) - 3
    except:
        duration_in_seconds = 0
    put = {
        "title": title,
        "dur": duration,
        "streamtype": stream,
        "by": user,
        "user_id": user_id,
        "chat_id": original_chat_id,
        "file": file,
        "vidid": vidid,
        "seconds": duration_in_seconds,
        "played": 0,
    }
    if forceplay:
        check = db.get(chat_id)
        if check:
            check.insert(0, put)
        else:
            db[chat_id] = []
            db[chat_id].append(put)
    else:
        db[chat_id].append(put)
    if len(db.get(chat_id) or []) > 1:
        _spawn_precache(title, vidid, stream == "video")
    autoclean.append(file)


async def put_queue_index(
    chat_id,
    original_chat_id,
    file,
    title,
    duration,
    user,
    vidid,
    stream,
    forceplay: Union[bool, str] = None,
):
    if "20.212.146.162" in vidid:
        try:
            dur = await asyncio.get_event_loop().run_in_executor(
                None, check_duration, vidid
            )
            duration = seconds_to_min(dur)
        except:
            duration = "ᴜʀʟ sᴛʀᴇᴀᴍ"
            dur = 0
    else:
        dur = 0
    put = {
        "title": title,
        "dur": duration,
        "streamtype": stream,
        "by": user,
        "chat_id": original_chat_id,
        "file": file,
        "vidid": vidid,
        "seconds": dur,
        "played": 0,
    }
    if forceplay:
        check = db.get(chat_id)
        if check:
            check.insert(0, put)
        else:
            db[chat_id] = []
            db[chat_id].append(put)
    else:
        db[chat_id].append(put)


# ©️ Copyright Reserved - @truenakshu  Saksham Swaroop

# ===========================================
# ©️ 2025 Saksham Swaroop (aka @truenakshu)
# 🔗 GitHub : https://github.com/VIP-saksham/KeyaraMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots 
