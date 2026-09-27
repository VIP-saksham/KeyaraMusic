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
import random
from typing import Dict, List, Union

from KeyaraMusic import LOGGER, YouTube
from KeyaraMusic.misc import db

_LOGGER = LOGGER(__name__)

MAX_MOOD_SECONDS = 20 * 60  # jukebox/2hr tracks skip - vibe short rakhte hain

# ---------------------------------------------------------------------------
#  MOOD SEARCH POOLS  (curated Hinglish/English/Punjabi query mixes)
# ---------------------------------------------------------------------------
MOOD_QUERIES: Dict[str, List[str]] = {
    "happy": [
        "happy punjabi songs", "bollywood dance hits", "feel good songs hindi",
        "diljit dosanjh hits", "happy vibe mashup", "good mood songs hindi",
    ],
    "sad": [
        "sad songs hindi lofi", "broken heart songs hindi", "b praak sad songs",
        "alone sad mashup", "emotional songs hindi", "sad lofi bollywood",
    ],
    "romantic": [
        "romantic songs hindi", "love mashup arijit singh", "bollywood love songs",
        "atif aslam love songs", "romantic lofi songs", "valentine special songs",
    ],
    "energy": [
        "workout songs hindi", "gym motivation punjabi songs", "party anthems bollywood",
        "hype mashup", "sidhu moose wala hits", "power boost songs",
    ],
    "chill": [
        "lofi hindi songs", "chill vibes mashup", "slowed reverb bollywood",
        "night lofi playlist", "soft acoustic hindi songs", "rain lofi bollywood",
    ],
    "focus": [
        "study lofi beats", "focus music instrumental", "deep work playlist",
        "instrumental flute bollywood", "ambient study music", "lofi concentration",
    ],
    "party": [
        "bollywood party songs", "nonstop dj mashup", "club hits punjabi",
        "wedding dance songs", "bhangra hits", "dj hard bollywood",
    ],
    "sleep": [
        "sleep music relaxing", "soft piano sleep", "night rain sounds music",
        "calm sleep lofi", "gentle guitar sleep music", "moonlight piano",
    ],
}

MOOD_EMOJIS: Dict[str, str] = {
    "happy": "😊", "sad": "🥺", "romantic": "💕", "energy": "🔥",
    "chill": "😌", "focus": "🎧", "party": "🎉", "sleep": "🌙",
}

# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _rand_query() -> str:
    pool = random.choice(list(MOOD_QUERIES.values()))
    return random.choice(pool)


def _dur_seconds(duration_min) -> Union[int, None]:
    """'MM:SS' / 'H:MM:SS' -> seconds (None if unparsable)."""
    try:
        parts = [int(x) for x in str(duration_min).split(":")]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except Exception:
        return None
    return None


def _add_to_queue(chat_id: int, item: dict, who: str, user_id: int) -> bool:
    """Append a queue entry; returns False if queue is full/invalid."""
    vidid = item.get("vidid")
    if not vidid:
        return False
    q = db.setdefault(chat_id, [])
    if len(q) >= 12:
        return False
    duration_min = item.get("duration_min") or "0:00"
    seconds = _dur_seconds(duration_min)
    q.append(
        {
            "title": str(item.get("title") or "Unknown").title(),
            "dur": duration_min,
            "streamtype": "audio",
            "by": who,
            "user_id": user_id,
            "chat_id": chat_id,
            "file": f"vid_{vidid}",
            "vidid": vidid,
            "seconds": (seconds - 3) if seconds else 0,
            "played": 0,
        }
    )
    return True


async def _fetch_track(query: str) -> Union[dict, None]:
    """Search via YouTube.track (HellAPI search + ydl fallback)."""
    try:
        details, _vidid = await YouTube.track(query)
        return details or None
    except Exception:
        return None


# ---------------------------------------------------------------------------
#  /mood track picking
# ---------------------------------------------------------------------------
async def pick_mood_tracks(mood: str, limit: int = 4) -> List[dict]:
    """Fetch up to `limit` tracks for a mood, preferring <=20min tracks."""
    queries = list(MOOD_QUERIES.get(mood, []))
    random.shuffle(queries)
    tracks: List[dict] = []
    for query in queries:
        if len(tracks) >= limit:
            break
        track = await _fetch_track(query)
        if not track or not track.get("vidid"):
            continue
        secs = _dur_seconds(track.get("duration_min"))
        if secs is not None and secs > MAX_MOOD_SECONDS:
            continue  # jukebox skip, next query try karo
        if any(t.get("vidid") == track["vidid"] for t in tracks):
            continue
        tracks.append(track)
        await asyncio.sleep(0.3)
    if not tracks:
        # sab lambi nikli -> filter hata do, kuch bhi le lo
        for query in queries:
            track = await _fetch_track(query)
            if track and track.get("vidid"):
                tracks.append(track)
                if len(tracks) >= limit:
                    break
            await asyncio.sleep(0.3)
    return tracks


# ---------------------------------------------------------------------------
#  /autoplay engine
# ---------------------------------------------------------------------------
async def queue_autoplay_next(chat_id: int) -> bool:
    """Auto-append the next song: related track of current, else random mood."""
    q = db.get(chat_id) or []
    if len(q) >= 2:
        return False
    item = None
    try:
        if q and q[0].get("vidid"):
            item = await YouTube.related(q[0]["vidid"])
    except Exception:
        item = None
    if not item or not item.get("vidid"):
        for _ in range(3):
            item = await _fetch_track(_rand_query())
            if item and item.get("vidid"):
                secs = _dur_seconds(item.get("duration_min"))
                if secs is None or secs <= MAX_MOOD_SECONDS:
                    break
            await asyncio.sleep(0.3)
    if not item or not item.get("vidid"):
        return False
    return _add_to_queue(chat_id, item, "Keyara Auto", 0)


async def ensure_autoplay_on_empty(chat_id: int) -> bool:
    """Called when queue is empty in change_stream. True = queued something."""
    from KeyaraMusic.utils.database import is_autoplay  # lazy: avoid cycles

    try:
        if not (await is_autoplay(chat_id)):
            return False
    except Exception:
        return False
    try:
        return await queue_autoplay_next(chat_id)
    except Exception as e:
        _LOGGER.warning(
            f"autoplay pick failed for {chat_id}: {type(e).__name__}: {e}"
        )
        return False


# Copyright (c) 2026 Saksham Swaroop - @truenakshu
