# KeyaraMusic — "iOS Now Playing" thumbnail engine
#
# Design: iOS lock-screen player jaisa feel —
#   1. Background: artwork blur + dark scrim (iOS glassy look)
#   2. Bada rounded-rect artwork with soft drop shadow
#   3. Center-aligned bada title (auto-shrink to fit), iOS typography
#   4. Secondary line: channel - views - duration
#   5. Progress bar + elapsed/total time labels
#   6. Playback controls row: prev / pause / next glyphs
#
# Deterministic: same video-ID = same poster.
# Robustness:
#   - Stylized titles (small-caps etc.) jo font me missing hain wo readable
#     ASCII me transliterate hote hain — title hamesha dikhta hai.
#   - app.username guard: client start nahi hua to fallback text.

import hashlib
import random
import traceback
from pathlib import Path

import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from KeyaraMusic import app
from py_yt import VideosSearch

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1320, 760

FONT_REGULAR_PATH = "KeyaraMusic/assets/font2.ttf"
FONT_BOLD_PATH = "KeyaraMusic/assets/font3.ttf"
DEFAULT_THUMB = "KeyaraMusic/assets/ShrutiBots.jpg"

LABEL = (255, 255, 255, 250)
SECONDARY = (235, 235, 245, 165)
TERTIARY = (235, 235, 245, 115)
TRACK = (255, 255, 255, 70)
FILL = (255, 255, 255, 235)

ART_SIZE = 360
ART_RADIUS = 82
MARGIN_X = 180

_FONT_CACHE = {}

_CHAR_MAP = {
    "ᴀ": "a", "ʙ": "b", "ᴄ": "c", "ᴅ": "d", "ᴇ": "e", "ꜰ": "f", "ɢ": "g",
    "ʜ": "h", "ɪ": "i", "ᴊ": "j", "ᴋ": "k", "ʟ": "l", "ᴍ": "m", "ɴ": "n",
    "ᴏ": "o", "ᴘ": "p", "ǫ": "q", "ʀ": "r", "ꜱ": "s", "ᴛ": "t", "ᴜ": "u",
    "ᴠ": "v", "ᴡ": "w", "x": "x", "ʏ": "y", "ᴢ": "z",
    "𝐀": "A", "𝐁": "B", "𝐂": "C", "𝐃": "D", "𝐄": "E", "𝐅": "F", "𝐆": "G",
    "𝐇": "H", "𝐈": "I", "𝐉": "J", "𝐊": "K", "𝐋": "L", "𝐌": "M", "𝐍": "N",
    "𝐎": "O", "𝐏": "P", "𝐐": "Q", "𝐑": "R", "𝐒": "S", "𝐓": "T", "𝐔": "U",
    "𝐕": "V", "𝐖": "W", "𝐗": "X", "𝐘": "Y", "𝐙": "Z",
    "𝐚": "a", "𝐛": "b", "𝐜": "c", "𝐝": "d", "𝐞": "e", "𝐟": "f", "𝐠": "g",
    "𝐡": "h", "𝐢": "i", "𝐣": "j", "𝐤": "k", "𝐥": "l", "𝐦": "m", "𝐧": "n",
    "𝐨": "o", "𝐩": "p", "𝐪": "q", "𝐫": "r", "𝐬": "s", "𝐭": "t", "𝐮": "u",
    "𝐯": "v", "𝐰": "w", "𝐱": "x", "𝐲": "y", "𝐳": "z",
    "’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-",
}


def _readable(text: str) -> str:
    """Transliterate stylized chars the font can't show; drop undrawables."""
    if not text:
        return text
    out = []
    changed = False
    for ch in text:
        if ch in _CHAR_MAP:
            out.append(_CHAR_MAP[ch])
            changed = True
        else:
            out.append(ch)
    txt = "".join(out)
    if changed or txt != text:
        txt = "".join(ch for ch in txt if ch.isascii() or ch in "éèêáàíóúñüöäç")
    return txt or text


def _bot_username() -> str:
    try:
        return app.username or "KeyaraMusicBot"
    except Exception:
        return "KeyaraMusicBot"


def _rng_for(videoid: str) -> random.Random:
    seed = int(hashlib.sha256(videoid.encode()).hexdigest()[:16], 16)
    return random.Random(seed)


def _font(path, size):
    key = (path, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(path, size)
    return _FONT_CACHE[key]


# ---------- background ------------------------------------------------------


def _cover_crop(img, w, h):
    scale = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1), Image.LANCZOS)
    x = (img.width - w) // 2
    y = (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def _ios_background(art):
    bg = _cover_crop(art, CANVAS_W, CANVAS_H).filter(ImageFilter.GaussianBlur(42))
    bg = ImageEnhance.Brightness(bg).enhance(0.48)
    bg = ImageEnhance.Color(bg).enhance(0.92)
    return bg.convert("RGBA")


def _scrim(canvas):
    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    stops = [(0.0, 70), (0.45, 40), (1.0, 130)]
    for y in range(CANVAS_H):
        t = y / CANVAS_H
        for (t0, a0), (t1, a1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0)
                alpha = int(a0 + (a1 - a0) * k)
                break
        d.line([(0, y), (CANVAS_W, y)], fill=(0, 0, 0, alpha))
    return Image.alpha_composite(canvas, overlay)


# ---------- artwork ---------------------------------------------------------


def _rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


def _artwork_with_shadow(canvas, art, x, y):
    size = ART_SIZE
    sh = Image.new("RGBA", (size + 120, size + 120), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [60, 60, 60 + size, 60 + size], radius=ART_RADIUS, fill=(0, 0, 0, 150)
    )
    sh = sh.filter(ImageFilter.GaussianBlur(26))
    canvas.alpha_composite(sh, (x - 60, y - 60 + 16))

    rounded = art.resize((size, size), Image.LANCZOS).convert("RGBA")
    rounded.putalpha(_rounded_mask(size, ART_RADIUS))
    canvas.alpha_composite(rounded, (x, y))


# ---------- typography ------------------------------------------------------


def _fit_title(draw, text, max_width):
    for size in (48, 42, 36, 31):
        font = _font(FONT_BOLD_PATH, size)
        if draw.textlength(text, font=font) <= max_width:
            return [text], font
    font = _font(FONT_BOLD_PATH, 31)
    words = text.split()
    while words and draw.textlength(" ".join(words) + "...", font=font) > max_width:
        words.pop()
    return [" ".join(words) + "..."], font


def _secondary_line(draw, channel, views, duration_label):
    parts = [channel, views, duration_label]
    font = _font(FONT_REGULAR_PATH, 30)
    text = "  -  ".join(p for p in parts if p)
    if draw.textlength(text, font=font) > CANVAS_W - 2 * MARGIN_X - 40:
        text = "  -  ".join([channel, duration_label])
    return text, font


# ---------- time + progress -------------------------------------------------


def _parse_seconds(duration):
    if not duration or ":" not in duration:
        return None
    try:
        parts = [int(p) for p in duration.split(":")]
    except ValueError:
        return None
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return None


def _fmt_time(sec):
    sec = max(0, int(sec))
    m, s = divmod(sec, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _progress_bar(canvas, x0, x1, y, progress):
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([x0, y, x1, y + 8], radius=4, fill=TRACK)
    fill_x = x0 + (x1 - x0) * progress
    if fill_x - x0 > 12:
        d.rounded_rectangle([x0, y, fill_x, y + 8], radius=4, fill=FILL)
    d.ellipse([fill_x - 9, y - 5, fill_x + 9, y + 13], fill=FILL)


# ---------- controls glyphs -------------------------------------------------


def _glyph_prev(d, cx, cy):
    tw, th, gap = 24, 40, 9
    x0 = cx - (2 * tw + gap) / 2
    for off in (0, tw + gap):
        bx = x0 + off + tw
        d.polygon([(bx, cy), (bx - tw, cy - th / 2), (bx - tw, cy + th / 2)], fill=LABEL)


def _glyph_next(d, cx, cy):
    tw, th, gap = 24, 40, 9
    x0 = cx - (2 * tw + gap) / 2
    for off in (0, tw + gap):
        bx = x0 + off
        d.polygon([(bx, cy), (bx + tw, cy - th / 2), (bx + tw, cy + th / 2)], fill=LABEL)


def _glyph_pause(d, cx, cy):
    bw, bh, gap = 13, 46, 15
    x0 = cx - (bw + gap / 2)
    for off in (0, bw + gap):
        d.rounded_rectangle(
            [x0 + off, cy - bh / 2, x0 + off + bw, cy + bh / 2], radius=6, fill=LABEL
        )


# ---------- main ------------------------------------------------------------


async def gen_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    raw_art_path = None
    try:
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "Unknown")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown Views")
        channel = result.get("channel", {}).get("name", "Unknown Channel")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumburl) as resp:
                    if resp.status == 200:
                        raw_art_path = CACHE_DIR / f"raw_{videoid}.png"
                        async with aiofiles.open(raw_art_path, "wb") as f:
                            await f.write(await resp.read())
        except Exception:
            raw_art_path = None

        if raw_art_path and Path(raw_art_path).exists():
            base_img = Image.open(raw_art_path).convert("RGBA")
        else:
            base_img = Image.open(DEFAULT_THUMB).convert("RGBA")

    except Exception as e:
        print(f"[gen_thumb Error - Using Default] {e}")
        try:
            base_img = Image.open(DEFAULT_THUMB).convert("RGBA")
            title = "KeyaraMusic"
            duration = "Unknown"
            views = "Unknown Views"
            channel = "KeyaraBots"
        except Exception:
            traceback.print_exc()
            return None

    try:
        rng = _rng_for(videoid)
        progress = rng.uniform(0.30, 0.80)

        title = _readable(title)
        channel = _readable(channel)
        views = _readable(views)

        canvas = _ios_background(base_img)
        canvas = _scrim(canvas)
        draw = ImageDraw.Draw(canvas)

        # ----- top mini label (player name) -----
        top_font = _font(FONT_REGULAR_PATH, 26)
        brand = _bot_username()
        tw = draw.textlength(brand, font=top_font)
        draw.text(((CANVAS_W - tw) / 2, 26), brand, font=top_font, fill=TERTIARY)

        # ----- artwork -----
        art_x = (CANVAS_W - ART_SIZE) // 2
        art_y = 76
        _artwork_with_shadow(canvas, base_img, art_x, art_y)
        draw = ImageDraw.Draw(canvas)

        # ----- title (auto-fit, centered) -----
        title_lines, title_font = _fit_title(draw, title, CANVAS_W - 2 * MARGIN_X)
        line_h = title_font.size + 12
        title_y = 470
        for i, ln in enumerate(title_lines):
            lw = draw.textlength(ln, font=title_font)
            draw.text(((CANVAS_W - lw) / 2, title_y + i * line_h), ln,
                      font=title_font, fill=LABEL)
        draw = ImageDraw.Draw(canvas)

        # ----- secondary line -----
        dur_label = duration if _parse_seconds(duration) is None else _fmt_time(
            _parse_seconds(duration)
        )
        sec_text, sec_font = _secondary_line(draw, channel, views, dur_label)
        sec_y = title_y + len(title_lines) * line_h + 14
        sw = draw.textlength(sec_text, font=sec_font)
        draw.text(((CANVAS_W - sw) / 2, sec_y), sec_text, font=sec_font, fill=SECONDARY)

        # ----- progress bar + times -----
        bar_x0, bar_x1, bar_y = MARGIN_X, CANVAS_W - MARGIN_X, 630
        _progress_bar(canvas, bar_x0, bar_x1, bar_y, progress)
        draw = ImageDraw.Draw(canvas)

        total = _parse_seconds(duration)
        time_font = _font(FONT_REGULAR_PATH, 24)
        if total:
            left_t, right_t = _fmt_time(progress * total), _fmt_time(total)
        else:
            left_t, right_t = "-", "LIVE"
        draw.text((bar_x0, bar_y + 18), left_t, font=time_font, fill=SECONDARY)
        rw = draw.textlength(right_t, font=time_font)
        draw.text((bar_x1 - rw, bar_y + 18), right_t, font=time_font, fill=SECONDARY)

        # ----- controls row -----
        cy = 706
        _glyph_prev(draw, 540, cy)
        _glyph_pause(draw, 660, cy)
        _glyph_next(draw, 780, cy)

        out = CACHE_DIR / f"{videoid}_final.png"
        canvas.convert("RGB").save(out, quality=95, optimize=True)

        if raw_art_path and Path(raw_art_path).exists():
            try:
                raw_art_path.unlink(missing_ok=True)
            except Exception:
                pass

        return str(out)

    except Exception as e:
        print(f"[gen_thumb Processing Error] {e}")
        traceback.print_exc()
        return None
