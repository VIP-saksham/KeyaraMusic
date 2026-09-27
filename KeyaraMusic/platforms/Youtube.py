"""
youtube.py  (KeyaraAPI edition — adapted for KeyaraMusic platforms/Youtube.py)
----------
KeyaraAPI — Drop-in replacement for the music bot's youtube.py

Setup:
  1. Copy this file over platforms/Youtube.py
  2. Add to .env:
       HELLAPI_URL=http://localhost:8000
       HELLAPI_KEY=HellAPIxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  3. Done — no other changes needed

Compatible with: AnonXMusic, YukkiMusic, SankiMusic, EnafulMusic,
                 any bot using YouTubeAPI class
"""

import asyncio
import os
import re
from urllib.parse import parse_qs, urlparse
from typing import Union

import aiohttp

# pyrogram OPTIONAL hai — sirf Message entity parsing ke liye.
# Koi bhi bot framework (pyrogram/telethon/discord.py/aiogram...) use kar sakta hai.
try:
    from pyrogram.enums import MessageEntityType
    from pyrogram.types import Message
    _HAS_PYROGRAM = True
except Exception:                     # pragma: no cover
    Message = object                  # type: ignore
    MessageEntityType = None          # type: ignore
    _HAS_PYROGRAM = False

# ── Config ───────────────────────────────────────────────────────────────────
API_URL = os.environ.get("HELLAPI_URL", "").rstrip("/")
API_KEY = os.environ.get("HELLAPI_KEY", "")

if not API_URL:
    raise EnvironmentError(
        "[KeyaraAPI] HELLAPI_URL not set.\n"
        "Add to .env:  HELLAPI_URL=http://your-server:8000"
    )
if not API_KEY:
    raise EnvironmentError(
        "[KeyaraAPI] HELLAPI_KEY not set.\n"
        "Add to .env:  HELLAPI_KEY=HellAPIxxxxxxxxxxxxxxxx\n"
        "Get key: @KeyaraApiBot → /start"
    )

_HEADERS  = {"x-api-key": API_KEY, "Connection": "keep-alive"}
_TIMEOUT  = aiohttp.ClientTimeout(total=60, connect=10)
_VTIMEOUT = aiohttp.ClientTimeout(total=120, connect=10)

DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "downloads")

# Connection pool — reuse connections for speed
_connector = None

def _get_connector():
    global _connector
    if _connector is None or _connector.closed:
        _connector = aiohttp.TCPConnector(
            limit=20,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
    return _connector


_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _normalise_video_url(value: str, videoid: Union[bool, str] = False) -> str:
    """Accept a YouTube URL or exact video ID; never treat text as a search."""
    raw = str(value or "").strip()
    if videoid:
        raw = raw.split("&", 1)[0].split("?", 1)[0]
        if not _VIDEO_ID_RE.fullmatch(raw):
            raise ValueError("Expected an 11-character YouTube video ID.")
        return f"https://www.youtube.com/watch?v={raw}"

    if _VIDEO_ID_RE.fullmatch(raw):
        return f"https://www.youtube.com/watch?v={raw}"
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if host == "youtu.be":
        candidate = parsed.path.strip("/").split("/", 1)[0]
    elif host.endswith("youtube.com"):
        if parsed.path == "/watch":
            candidate = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/")):
            candidate = parsed.path.split("/")[2]
        else:
            candidate = ""
    else:
        candidate = ""
    if not _VIDEO_ID_RE.fullmatch(candidate):
        raise ValueError(
            "Only a YouTube video URL or 11-character video ID is supported; "
            "song-name search is disabled."
        )
    return f"https://www.youtube.com/watch?v={candidate}"


def _video_id(value: str, videoid: Union[bool, str] = False) -> str:
    return parse_qs(urlparse(_normalise_video_url(value, videoid)).query)["v"][0]


# ── Standalone functions (direct imports) ────────────────────────────────────

async def download_song(link: str) -> str:
    """Return instant KeyaraAPI stream URL (no download). Falls back to file on failure."""
    try:
        video_id = _video_id(link)
    except ValueError:
        return None
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path
    try:
        data = await _api_get("/api/stream", {
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "type": "audio"
        })
        stream_url = data.get("stream_url") or data.get("direct_url")
        return stream_url or None
    except Exception:
        return None


async def download_video(link: str) -> str:
    """Return instant KeyaraAPI stream URL (no download). Falls back to file on failure."""
    try:
        video_id = _video_id(link)
    except ValueError:
        return None
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path
    try:
        data = await _api_get("/api/stream", {
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "type": "video"
        }, timeout=_VTIMEOUT)
        stream_url = data.get("stream_url") or data.get("direct_url")
        return stream_url or None
    except Exception:
        return None


# ── Internal helpers ──────────────────────────────────────────────────────────

def _time_to_seconds(time_str: str) -> int:
    try:
        parts = [int(x) for x in str(time_str).split(":")]
        return sum(x * (60 ** i) for i, x in enumerate(reversed(parts)))
    except Exception:
        return 0


def _seconds_to_min(seconds) -> str:
    try:
        m, s = divmod(int(seconds or 0), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
    except Exception:
        return "0:00"


# Yukki/AnonX-style bots ye bina-underscore naam import karte hain
seconds_to_min = _seconds_to_min


async def _ydl_search(query: str, limit: int = 1) -> list:
    """
    Yukki/AnonX-style platform files (Apple.py, Resso.py, etc.) isse import
    karti hain — song-name se YouTube pe search karta hai (HellAPI /search).

    Returns list of dicts with common keys:
      id/vidid, title, link/url, duration, duration_min, thumb/thumbnail
    """
    try:
        data = await _api_get("/search", {"q": query, "limit": max(1, min(int(limit), 10))})
    except Exception:
        return []

    results = []
    for r in data.get("results", []):
        vid = r.get("id") or ""
        if not vid:
            continue
        results.append({
            "id":           vid,
            "vidid":        vid,
            "title":        r.get("title") or "Unknown",
            "link":         r.get("url") or f"https://www.youtube.com/watch?v={vid}",
            "url":          r.get("url") or f"https://www.youtube.com/watch?v={vid}",
            "duration":     r.get("duration"),
            "duration_min": _seconds_to_min(r.get("duration")),
            "thumb":        r.get("thumbnail") or "",
            "thumbnail":    r.get("thumbnail") or "",
        })
    return results


def _cleanup(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


async def _api_get(path: str, params: dict, timeout=None, retries: int = 2) -> dict:
    """GET request to HellAPI with auto-retry on failure."""
    url = f"{API_URL}{path}"
    last_exc = None
    for attempt in range(retries + 1):
        try:
            async with aiohttp.ClientSession(
                connector=_get_connector(),
                connector_owner=False,
            ) as session:
                async with session.get(
                    url,
                    params=params,
                    headers=_HEADERS,
                    timeout=timeout or _TIMEOUT,
                ) as resp:
                    if resp.status == 401:
                        raise PermissionError(
                            "HellAPI key invalid/expired. "
                            "Get new key from HellAPI bot → /start"
                        )
                    if resp.status == 429:
                        data = await resp.json()
                        msg  = (data.get("detail") or {}).get("message", "Rate limit exceeded.")
                        raise ConnectionAbortedError(f"Rate limit: {msg}")
                    if resp.status == 503:
                        raise ConnectionError("YouTube IP block. Retry in a few minutes.")
                    if resp.status != 200:
                        text = await resp.text()
                        raise ConnectionError(f"HellAPI {resp.status}: {text[:100]}")
                    return await resp.json()
        except (PermissionError, ConnectionAbortedError):
            raise   # Don't retry auth/rate limit errors
        except Exception as e:
            last_exc = e
            if attempt < retries:
                await asyncio.sleep(1.5 * (attempt + 1))
    raise last_exc or ConnectionError("HellAPI request failed")


async def _download_file(url: str, path: str, timeout=None):
    """Stream download URL to disk."""
    async with aiohttp.ClientSession(
        connector=_get_connector(),
        connector_owner=False,
    ) as session:
        async with session.get(url, timeout=timeout or _VTIMEOUT) as resp:
            if resp.status != 200:
                raise ConnectionError(f"Download failed: HTTP {resp.status}")
            with open(path, "wb") as f:
                async for chunk in resp.content.iter_chunked(131072):
                    f.write(chunk)


# ── YouTubeAPI class ──────────────────────────────────────────────────────────

class YouTubeAPI:

    def __init__(self):
        self.base     = "https://www.youtube.com/watch?v="
        self.regex    = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        self.reg      = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def name(self, link: str, videoid: Union[bool, str] = None):
        """
        Yukki-style: song-NAME ya URL/ID → (track_details, vidid)
        SHUKLAMUSIC/Yukki ka /play handler pehle YHI call karta hai.
        track_details = {title, link, vidid, duration_min}
        """
        if videoid:
            link = self.base + link

        # Case 1: URL ya 11-char video ID
        try:
            vidid = _video_id(link)
            watch = f"https://www.youtube.com/watch?v={vidid}"
            data  = await _api_get("/info", {"url": watch})
            d = data.get("data", {})
            return {
                "title":        d.get("title") or "Unknown",
                "link":         watch,
                "vidid":        vidid,
                "duration_min": _seconds_to_min(d.get("duration_seconds")),
            }, vidid
        except ValueError:
            pass   # song-name hai, URL nahi — niche search karo

        # Case 2: song-name → HellAPI /search
        results = await _ydl_search(link, limit=1)
        if not results:
            raise ValueError(f"No results found for: {link}")
        r = results[0]
        return {
            "title":        r["title"],
            "link":         r["link"],
            "vidid":        r["id"],
            "duration_min": r["duration_min"],
        }, r["id"]

    async def exists(self, link: str, videoid: Union[bool, str] = None) -> bool:
        try:
            _normalise_video_url(link, videoid)
            return True
        except ValueError:
            return False

    async def url(self, message_1) -> Union[str, None]:
        """Message se pehla URL nikalo (pyrogram Message hi pass karo)."""
        if not _HAS_PYROGRAM:
            return None
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    def _clean(self, link: str) -> str:
        return link.split("&")[0] if "&" in link else link

    async def details(self, link: str, videoid: Union[bool, str] = None):
        """Returns: title, duration_min, duration_sec, thumbnail, vidid"""
        link = _normalise_video_url(link, videoid)
        data = await _api_get("/info", {"url": link})
        d = data.get("data", {})
        title = d.get("title") or "Unknown"
        duration_sec = int(d.get("duration_seconds") or 0)
        duration_min = _seconds_to_min(duration_sec)
        thumbnail = d.get("thumbnail") or ""
        vidid = d.get("id") or _video_id(link)
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None) -> str:
        t, *_ = await self.details(link, videoid)
        return t

    async def duration(self, link: str, videoid: Union[bool, str] = None) -> str:
        _, d, *_ = await self.details(link, videoid)
        return d

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None) -> str:
        _, _, _, t, _ = await self.details(link, videoid)
        return t

    async def track(self, link: str, videoid: Union[bool, str] = None):
        """Returns: track_details dict, vidid. Song-name query bhi accept karta hai."""
        if not videoid:
            # URL / video-ID try karo; warna song-name search fallback
            try:
                link = _normalise_video_url(link)
            except ValueError:
                results = await _ydl_search(str(link), limit=1)
                if not results:
                    raise ValueError(f"No results found for: {link}")
                r = results[0]
                return {
                    "title":        r["title"],
                    "link":         r["link"],
                    "vidid":        r["id"],
                    "duration_min": r["duration_min"],
                    "thumb":        r["thumbnail"],
                }, r["id"]
        else:
            link = _normalise_video_url(link, videoid)
        data = await _api_get("/info", {"url": link})
        d = data.get("data", {})
        title = d.get("title") or "Unknown"
        vidid = d.get("id") or _video_id(link)
        duration_min = _seconds_to_min(d.get("duration_seconds"))
        thumbnail = d.get("thumbnail") or ""
        yturl = link
        return {
            "title":        title,
            "link":         yturl,
            "vidid":        vidid,
            "duration_min": duration_min,
            "thumb":        thumbnail,
        }, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        """Returns: formats_list, link"""
        link = _normalise_video_url(link, videoid)
        data = await _api_get("/formats", {"url": link})
        result = []
        for f in data.get("formats", []):
            fmt_str = f.get("resolution") or f.get("ext") or ""
            if "dash" in fmt_str.lower():
                continue
            result.append({
                "format":      f"{f.get('format_id')} - {fmt_str}",
                "filesize":    f.get("filesize_approx"),
                "format_id":   f.get("format_id"),
                "ext":         f.get("ext"),
                "format_note": f.get("resolution") or "",
                "yturl":       link,
            })
        return result, link

    async def slider(self, link: str, query_type: int,
                     videoid: Union[bool, str] = None):
        """Return details for a URL; title search is intentionally disabled."""
        if not videoid and not re.search(self.regex, str(link or "")):
            raise ValueError("Song-name search is disabled; provide a YouTube URL.")
        title, duration, _, thumbnail, vidid = await self.details(link, videoid)
        return title, duration, thumbnail, vidid

    async def playlist(self, link, limit, user_id,
                       videoid: Union[bool, str] = None):
        """
        Yukki-style: list of (title, duration_min, url, vidid) tuples.
        HellAPI playlist-entries extract nahi karta — graceful [] fallback.
        """
        if videoid:
            link = self.listbase + link
        link = self._clean(link)
        try:
            data    = await _api_get("/info", {"url": link}, retries=0)
            entries = data.get("data", {}).get("entries", []) or []
            out = []
            for e in entries[: max(1, int(limit))]:
                if not isinstance(e, dict) or not e.get("id"):
                    continue
                vidid = e["id"]
                title = e.get("title") or "Unknown"
                dur   = e.get("duration_seconds") or e.get("duration") or 0
                out.append((title, _seconds_to_min(dur), self.base + vidid, vidid))
            if out:
                return out
        except Exception:
            pass
        return []

    async def related(self, videoid: str,
                      exclude_ids: Union[list, set, None] = None):
        """Returns next recommended track dict or None."""
        exclude = set(exclude_ids or [])
        exclude.add(videoid)
        try:
            info      = await _api_get("/info", {"url": self.base + videoid})
            seed_title = info.get("data", {}).get("title", "")
            if not seed_title:
                return None
            search = await _api_get("/search", {"q": seed_title, "limit": 10})
            for r in search.get("results", []):
                vid = r.get("id")
                dur = r.get("duration")
                if vid and dur and vid not in exclude:
                    return {
                        "title":        r.get("title", "Unknown"),
                        "vidid":        vid,
                        "duration_min": _seconds_to_min(dur),
                        "thumb":        r.get("thumbnail", ""),
                        "link":         r.get("url", self.base + vid),
                    }
        except Exception:
            pass
        return None

    async def video(self, link: str, videoid: Union[bool, str] = None):
        """Returns: (1, file_path) or (0, error_msg)"""
        try:
            link = _normalise_video_url(link, videoid)
            data       = await _api_get("/api/stream",
                                        {"url": link, "type": "video"},
                                        timeout=_VTIMEOUT)
            stream_url = data.get("stream_url") or data.get("direct_url")
            if not stream_url:
                return 0, "No stream URL"
            vid_id    = _video_id(link)
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            file_path = os.path.join(DOWNLOAD_DIR, f"{vid_id}.mp4")
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return 1, file_path
            await _download_file(stream_url, file_path, timeout=_VTIMEOUT)
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return 1, file_path
            return 0, "Empty file"
        except Exception as e:
            return 0, str(e)

    async def download(
        self,
        link: str,
        mystic,
        video:     Union[bool, str] = None,
        videoid:   Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title:     Union[bool, str] = None,
    ) -> tuple:
        """
        Main download — used by /play, /vplay. Returns (path, True) or (None, False).
        ⚡ SPEED MODE: full-file download skip — HellAPI ka stream URL direct
        return karta hai (direct=True). py-tgcalls URL ko live-stream karta hai,
        isliye VC me 1-2 sec me play start ho jata hai.
        """
        try:
            if format_id:
                link = _normalise_video_url(link, videoid)
                data = await _api_get("/ytdl",
                                      {"url": link, "format": str(format_id)},
                                      timeout=_VTIMEOUT)
                stream_url = (data.get("stream_url")
                              or data.get("direct_url")
                              or data.get("url"))
                if not stream_url:
                    return None, False
                vid_id    = _video_id(link)
                ext       = data.get("ext") or "mp4"
                os.makedirs(DOWNLOAD_DIR, exist_ok=True)
                file_path = os.path.join(DOWNLOAD_DIR, f"{vid_id}.{ext}")
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    return file_path, True
                await _download_file(stream_url, file_path, timeout=_VTIMEOUT)
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    return file_path, True
                return None, False

            media_type = "video" if (video or songvideo) else "audio"
            link = _normalise_video_url(link, videoid)
            data = await _api_get("/api/stream",
                                  {"url": link, "type": media_type},
                                  timeout=_VTIMEOUT)
            stream_url = (data.get("stream_url")
                          or data.get("direct_url")
                          or data.get("url"))
            if not stream_url:
                return None, False

            # ⚡ SPEED MODE — URL hi return karo, download skip
            return stream_url, True

        except Exception:
            return None, False


# ── Singleton ─────────────────────────────────────────────────────────────────
YouTube = YouTubeAPI()
