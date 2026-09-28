# =============================================================================
#  Copyright (c) 2026 Saksham Swaroop (@truenakshu)  |  GitHub: VIP-saksham
#  LinkedIn: sakshamswaroop
#
#  All rights reserved. This source code is the private property of the
#  author. Copying, modifying, redistributing or deploying any part of this
#  file WITHOUT the author's written permission is strictly prohibited.
#  For licensing / permission: https://t.me/truenakshu
# =============================================================================
#
#  tgsongs — Telegram song-library engine (server-search based)
#  Assistant userbot @YouTube_Downs (jaise 130k-song channel) me Telegram ke
#  server-side search se audio dhundta hai, best match download karke local
#  file ke roop me return karta hai — jo VC me direct stream hota hai.
#  No yt-dlp, no external API => instant playback. Miss par caller apne
#  normal YouTube/API path par fallback karta hai.
#

import json
import os
import re

from KeyaraMusic.logging import LOGGER

_LOG = LOGGER(__name__)

# Library channel (.env: TG_SONGS_CHANNEL se override)
TG_SONGS_CHANNEL = (
    os.environ.get("TG_SONGS_CHANNEL", "YouTube_Downs")
    .lstrip("@")
    .strip()
)

# Match score threshold (Jaccard word-overlap)
_SCORE_MIN = 0.45

# Query/filename noise words
_STOPWORDS = {
    "official", "video", "audio", "music", "song", "songs", "full",
    "lyrical", "lyrics", "lyric", "hd", "4k", "1080p", "720p", "feat",
    "ft", "remix", "cover", "version", "new", "latest", "the", "a", "an",
    "from", "movie", "film", "album", "single", "promo", "teaser", "trailer",
    "128kbps", "320kbps", "kbps", "mp3", "128", "320",
}

_nonword_re = re.compile(r"[^a-z0-9 ]+")

# Downloaded files jo cache me rahenge (auto_clean inhe delete nahi karega)
# -> repeat plays = 0s download = 1-2s me VC me play
_PERSISTENT = set()


def is_persistent(path: str) -> bool:
    """auto_clean ke liye: ye file cached-library file hai (delete mat karo)?"""
    return path in _PERSISTENT


# Query->filename map (json persisted): repeat plays bina Telegram search ke
_MAP_FILE = os.path.join(os.path.abspath("downloads"), ".tg_songs_map.json")
_qmap = {}
try:
    with open(_MAP_FILE, "r", encoding="utf-8") as _f:
        _qmap = json.load(_f)
except Exception:
    _qmap = {}


def _map_key(query: str) -> str:
    return " ".join(sorted(_query_words(query)))


def _map_save():
    try:
        os.makedirs(os.path.dirname(_MAP_FILE), exist_ok=True)
        with open(_MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(_qmap, f, ensure_ascii=False)
    except Exception:
        pass


async def get_cached(query: str):
    """Pehle play ho chuka gaana? -> local path (bina kisi network call ke)."""
    fn = _qmap.get(_map_key(query))
    if not fn:
        return None
    path = os.path.join(os.path.abspath("downloads"), fn)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        _PERSISTENT.add(path)
        _LOG.info(f"tgsongs: instant cache hit — {fn}")
        return path
    return None


def _clean_filename(fn: str) -> str:
    """'Kesariya_(Official_Audio).mp3' -> 'kesariya official audio'"""
    base = os.path.splitext(os.path.basename(fn or ""))[0]
    base = re.sub(r"[_\-.()\[\]]+", " ", base)
    base = _nonword_re.sub(" ", base.lower())
    return " ".join(base.split())


def _query_words(query: str):
    """Query words minus stopwords."""
    q = _nonword_re.sub(" ", (query or "").lower())
    return {w for w in q.split() if w and w not in _STOPWORDS}


async def find_audio_message(client, query: str):
    """Library channel me server-side search; best-scoring audio Message ya None."""
    from pyrogram.enums import MessagesFilter

    qwords = _query_words(query)
    if not qwords:
        return None
    q = " ".join(sorted(qwords)[:6])

    best, best_score = None, 0.0
    try:
        async for m in client.search_messages(
            TG_SONGS_CHANNEL, limit=30, filter=MessagesFilter.AUDIO, query=q
        ):
            aud = getattr(m, "audio", None)
            if not (aud and aud.file_name):
                continue
            twords = set(_clean_filename(aud.file_name).split()) - _STOPWORDS
            inter = len(qwords & twords)
            if not inter:
                continue
            score = inter / (len(qwords) + len(twords) - inter)
            if score > best_score:
                best, best_score = m, score
    except Exception as e:
        _LOG.warning(
            f"tgsongs: search failed in {TG_SONGS_CHANNEL}: {type(e).__name__}: {e}"
        )
        return None

    if best and best_score >= _SCORE_MIN:
        _LOG.info(
            f"tgsongs: '{query}' -> '{best.audio.file_name}' (score {best_score:.2f})"
        )
        return best
    return None


async def download_song(
    client, query: str, download_dir: str = "downloads", msg=None
):
    """Library se matched audio download karke local path return karo, ya None.
    msg pre-found ho to duplicate search skip (speed)."""
    try:
        if msg is None:
            msg = await find_audio_message(client, query)
        if msg is None:
            return None

        file_name = (msg.audio.file_name or "song.mp3")
        os.makedirs(download_dir, exist_ok=True)
        safe_name = file_name.replace("/", "-").replace("\\", "-")
        path = os.path.join(os.path.abspath(download_dir), safe_name)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            _PERSISTENT.add(path)
            _LOG.info(f"tgsongs: cached hit — {safe_name}")
            return path

        got = await client.download_media(msg, file_name=path)
        if got and os.path.getsize(got) > 0:
            _LOG.info(f"tgsongs: downloaded — {safe_name}")
            _PERSISTENT.add(os.path.abspath(got))
            _qmap[_map_key(query)] = safe_name
            _map_save()
            return got
        return None
    except Exception as e:
        _LOG.warning(f"tgsongs: download_song failed: {type(e).__name__}: {e}")
        return None


# �? Copyright Reserved - @truenakshu  Saksham Swaroop
