"""
autofix_agent.py
----------------
🤖 KeyaraMusic Self-Heal Agent (NVIDIA NIM powered)

Kya karta hai:
  1. log.txt ko live watch karta hai (tail-f style).
  2. Naya Python traceback dikhe to uska exception extract karke
     NVIDIA NIM (integrate.api.nvidia.com) ke LLM ko bhejta hai.
  3. AI ka root-cause + fix Hinglish me LOG_GROUP_ID me bhej deta hai
     aur autofix_history.log me save karta hai.
  4. Agar NVIDIA_API_KEY .env me nahi hai → agent disable ho jata hai
     (bot pe koi asar nahi).

Wire-up: KeyaraMusic/__main__.py ke init() me, idle() se pehle:
    from KeyaraMusic.utils.autofix_agent import start_autofix_agent
    start_autofix_agent()
"""

import os
import re
import time
import json
import asyncio
import aiohttp
import logging

log = logging.getLogger("autofix_agent")

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()
NVIDIA_BASE = os.getenv(
    "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
).rstrip("/")
NVIDIA_MODEL = os.getenv(
    "NVIDIA_MODEL", "meta/llama-3.3-70b-instruct"
)
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "0") or 0)
LOG_FILE = os.path.join(os.getcwd(), "log.txt")
HISTORY_FILE = os.path.join(os.getcwd(), "autofix_history.log")

POLL_SEC = int(os.getenv("AUTOFIX_POLL_SEC", "3"))
COOLDOWN_SEC = 120          # same error dobara report na ho iske andar
MAX_TB_CHARS = 3500         # LLM ko itna hi bhejenge

_ENABLED = bool(NVIDIA_API_KEY)

_SYSTEM_PROMPT = (
    "Tum ek expert Python + Telegram-bot (pyrogram/py-tgcalls) debugging assistant ho. "
    "User tumhe ek traceback dikhayega jo ek Telegram music bot (KeyaraMusic) ke "
    "log se aaya hai. Tumhe HINGLISH me, chhote aur clear jawab dena hai, exactly is "
    "format me (Telegram-friendly, HTML-safe, < b > tags use mat karo):\n\n"
    "🔴 ERROR: <exception ka naam + 1 line matlab>\n"
    "🧠 WAJAH: <root cause 1-2 line>\n"
    "🛠️ FIX: <exact kya karna hai, 1-3 steps / chhota code patch>\n"
    "⚠️ RISK: <low/medium/high + 1 line kyun>\n\n"
    "Jawab 180 words se chhota rakho. Speculation mat karo — sirf traceback se jo "
    "pata hai wahi batao. Agar traceback se reason clear nahi, to sabse likely "
    "reason batao aur usko 'likely' bol kar batao."
)

# Traceback detector
_TB_RE = re.compile(
    r"(Traceback \(most recent call last\):(?:\n.*)+?\n(?P<exc>[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception|Interrupt|Warning))(?::[^\n]*)?)",
    re.MULTILINE,
)

# In errors pe full traceback nahi bhejna, sirf naam kaafi hai
_FATAL_HINTS = (
    "SyntaxError", "ImportError", "ModuleNotFoundError",
    "KeyboardInterrupt", "SystemExit", "MongoServerSelectionError",
    "MongoConnectionFailure", "ServerSelectionTimeoutError",
)


def _extract_error(text: str):
    """Log chunk se last traceback (exc-name + block) nikalo."""
    matches = list(_TB_RE.finditer(text))
    if not matches:
        return None
    m = matches[-1]
    exc_name = m.group("exc")
    block = m.group(0)
    # traceback bada ho to sirf tail (last 60 lines) bhejo
    lines = block.splitlines()
    if len(lines) > 60:
        block = "\n".join(lines[:5] + ["... [snip] ..."] + lines[-40:])
    return exc_name, block[:MAX_TB_CHARS]


class AutofixAgent:
    def __init__(self):
        self.app = None            # pyrogram Client, start_autofix_agent() me set hota hai
        self._pos = None           # log.txt read offset
        self._cooldown = {}        # exc_name -> last ts
        self._last_ai_call = 0.0
        self._ai_min_gap = 10      # LLM rate-guard

    # ── log watching ─────────────────────────────────────────────
    def _read_new(self) -> str:
        try:
            size = os.path.getsize(LOG_FILE)
            if self._pos is None:
                # pehli baar: purana log skip, sirf tail yaad rakho
                self._pos = max(0, size - 4096)
                return ""
            if size < self._pos:          # log rotate
                self._pos = 0
            if size == self._pos:
                return ""
            with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self._pos)
                data = f.read()
            self._pos = f.tell()
            return data
        except FileNotFoundError:
            return ""
        except Exception:
            return ""

    # ── NVIDIA NIM call ──────────────────────────────────────────
    async def _ask_nvidia(self, traceback_text: str) -> str:
        payload = {
            "model": NVIDIA_MODEL,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Ye KeyaraMusic bot ke log.txt se nikla hai:\n\n"
                        f"{traceback_text}"
                    ),
                },
            ],
            "temperature": 0.2,
            "top_p": 0.9,
            "max_tokens": 400,
        }
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        timeout = aiohttp.ClientTimeout(total=45, connect=10)
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{NVIDIA_BASE}/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=timeout,
            ) as r:
                if r.status != 200:
                    body = (await r.text())[:200]
                    raise RuntimeError(f"NIM HTTP {r.status}: {body}")
                data = await r.json()
                return (data.get("choices", [{}])[0]
                              .get("message", {})
                              .get("content", "")).strip()

    # ── reporting ────────────────────────────────────────────────
    async def _report(self, exc_name: str, tb_block: str, advice: str):
        stamp = time.strftime("%d-%b-%y %H:%M:%S")
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(
                f"\n[{stamp}] {exc_name}\n{tb_block}\n--- AI ---\n{advice}\n"
            )

        if not self.app or not LOG_GROUP_ID:
            return
        text = (
            "🤖 <b>AUTO-FIX AGENT</b>\n"
            f"🕒 <code>{stamp}</code>\n\n"
            f"{advice}\n\n"
            f"📄 <b>Traceback (tail):</b>\n"
            f"<pre>{tb_block[-1200:]}</pre>"
        )
        try:
            await self.app.send_message(LOG_GROUP_ID, text[:4000])
        except Exception as e:
            log.warning("log-group send failed: %s", e)

    # ── main loop ────────────────────────────────────────────────
    async def run(self):
        log.info("Self-Heal Agent started (model=%s, file=%s)", NVIDIA_MODEL, LOG_FILE)
        while True:
            try:
                await asyncio.sleep(POLL_SEC)
                chunk = self._read_new()
                if not chunk:
                    continue
                hit = _extract_error(chunk)
                if not hit:
                    continue
                exc_name, block = hit
                now = time.time()
                if now - self._cooldown.get(exc_name, 0) < COOLDOWN_SEC:
                    continue
                if now - self._last_ai_call < self._ai_min_gap:
                    continue

                # fatal errors pe AI call ki zaroorat nahi — seedha report
                if any(h in exc_name for h in _FATAL_HINTS):
                    advice = (
                        f"🔴 ERROR: {exc_name}\n"
                        "🧠 WAJAH: Bot startup/core code ka fatal error — "
                        "ye process level issue hai.\n"
                        "🛠️ FIX: log.txt ka full traceback dekho; module missing ho "
                        "to 'pip install' karo, syntax ho to us file patch karo, "
                        "Mongo ho to mongod/URI check karo.\n"
                        "⚠️ RISK: high"
                    )
                    self._last_ai_call = now
                else:
                    try:
                        advice = await self._ask_nvidia(block)
                        self._last_ai_call = now
                        if not advice:
                            advice = f"🔴 ERROR: {exc_name}\n(NIM ne khali jawab diya)"
                    except Exception as e:
                        advice = (
                            f"🔴 ERROR: {exc_name}\n"
                            f"⚠️ AI offline tha ({str(e)[:80]}) — traceback dekho."
                        )
                        self._last_ai_call = now

                self._cooldown[exc_name] = now
                await self._report(exc_name, block, advice)
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(5)


_agent = AutofixAgent()


def start_autofix_agent(app):
    """__main__.py se call karo: app = pyrogram bot Client."""
    if not _ENABLED:
        log.warning(
            "Self-Heal Agent DISABLED — NVIDIA_API_KEY .env me set karo "
            "(https://build.nvidia.com se free key milti hai)."
        )
        return None
    _agent.app = app
    return asyncio.get_event_loop().create_task(_agent.run())
