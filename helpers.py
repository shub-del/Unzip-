"""
╔══════════════════════════════════════════════════════════╗
║           UNZIP BOT — utils/helpers.py                   ║
║  Shared utility functions.                               ║
╚══════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import asyncio
import math
import os
import shutil
import time
from pathlib import Path
from typing import Callable

import humanize
from loguru import logger


# ─── Progress Bar ─────────────────────────────────────────────────────────────

def make_progress_bar(percent: float, length: int = 12) -> str:
    """Return a Unicode progress bar string.

    e.g.  ████████░░░░  67%
    """
    filled = math.floor(length * percent / 100)
    bar = "█" * filled + "░" * (length - filled)
    return bar


# ─── Size / Time Formatters ──────────────────────────────────────────────────

def fmt_size(num_bytes: int) -> str:
    return humanize.naturalsize(num_bytes, binary=True)


def fmt_speed(bytes_per_sec: float) -> str:
    return humanize.naturalsize(bytes_per_sec, binary=True)


def fmt_elapsed(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"


def fmt_eta(remaining_bytes: int, speed: float) -> str:
    if speed <= 0:
        return "∞"
    secs = remaining_bytes / speed
    return fmt_elapsed(secs)


# ─── Directory Helpers ────────────────────────────────────────────────────────

def ensure_dirs(*dirs: str) -> None:
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def safe_remove(path: str | Path) -> None:
    """Remove a file or directory tree, ignoring errors."""
    try:
        p = Path(path)
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        elif p.exists():
            p.unlink(missing_ok=True)
    except Exception as exc:
        logger.warning("safe_remove {}: {}", path, exc)


async def auto_delete(path: str | Path, delay: int) -> None:
    """Delete path after `delay` seconds (non-blocking)."""
    await asyncio.sleep(delay)
    safe_remove(path)
    logger.debug("Auto-deleted: {}", path)


def dir_size(path: str | Path) -> int:
    """Return total bytes in a directory tree."""
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def list_files_recursive(path: str | Path) -> list[Path]:
    """Return all files under path, sorted."""
    return sorted(p for p in Path(path).rglob("*") if p.is_file())


# ─── Archive Detection ────────────────────────────────────────────────────────

def is_multipart_zip(filename: str) -> bool:
    """Detect .zip.001 / .z01 / .z02 … patterns."""
    name = filename.lower()
    return name.endswith(".zip.001") or name.endswith(".z01")


def is_multipart_rar(filename: str) -> bool:
    """Detect .part1.rar / .part01.rar patterns."""
    import re
    return bool(re.search(r"\.part0*1\.rar$", filename, re.IGNORECASE))


def get_archive_type(filename: str) -> str | None:
    """Return canonical archive type or None if unrecognised."""
    name = filename.lower()
    for ext in (".tar.gz", ".tar.bz2", ".tar.xz"):
        if name.endswith(ext):
            return ext
    for ext in (".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz", ".tbz2", ".txz"):
        if name.endswith(ext):
            return ext
    # multi-part
    if is_multipart_zip(name) or is_multipart_rar(name):
        return ".rar" if "rar" in name else ".zip"
    return None


# ─── Async Rate-limited Progress Callback Factory ────────────────────────────

def make_progress_callback(
    update_fn: Callable[[int, int], None],
    interval: float = 3.0,
) -> Callable[[int, int], None]:
    """
    Return a callback(current, total) that calls update_fn at most every
    `interval` seconds to avoid Telegram flood limits.
    """
    last: list[float] = [0.0]

    def callback(current: int, total: int) -> None:
        now = time.monotonic()
        if now - last[0] >= interval or current == total:
            last[0] = now
            update_fn(current, total)

    return callback


# ─── Inline Keyboard Builders (returned as raw dicts for Pyrogram) ────────────

def kb_start() -> list[list[dict]]:
    """Main /start inline keyboard."""
    return [
        [
            {"text": "📖 Help",      "callback_data": "help"},
            {"text": "⚙️ Settings",  "callback_data": "settings"},
        ],
        [
            {"text": "👑 Premium",   "callback_data": "premium_info"},
            {"text": "📊 Stats",     "callback_data": "my_stats"},
        ],
        [
            {"text": "🌐 Language",  "callback_data": "choose_lang"},
        ],
    ]


def kb_force_sub(invite_link: str) -> list[list[dict]]:
    return [
        [{"text": "📢 Join Channel", "url": invite_link}],
        [{"text": "✅ Joined",       "callback_data": "check_sub"}],
    ]


def kb_mode_select(current: str) -> list[list[dict]]:
    doc_mark  = "✅ " if current == "document" else ""
    med_mark  = "✅ " if current == "media"    else ""
    return [
        [
            {"text": f"{doc_mark}📄 Document", "callback_data": "mode_document"},
            {"text": f"{med_mark}🎬 Media",    "callback_data": "mode_media"},
        ],
        [{"text": "🔙 Back", "callback_data": "settings"}],
    ]


def kb_lang_select() -> list[list[dict]]:
    return [
        [
            {"text": "🇬🇧 English", "callback_data": "lang_en"},
            {"text": "🇮🇳 हिन्दी",  "callback_data": "lang_hi"},
        ],
        [{"text": "🔙 Back", "callback_data": "settings"}],
    ]


def kb_cancel() -> list[list[dict]]:
    return [[{"text": "🛑 Cancel", "callback_data": "cancel_task"}]]


def kb_settings() -> list[list[dict]]:
    return [
        [
            {"text": "📤 Upload Mode", "callback_data": "choose_mode"},
            {"text": "🌐 Language",    "callback_data": "choose_lang"},
        ],
        [
            {"text": "🖼️ Thumbnail",  "callback_data": "thumb_menu"},
        ],
        [{"text": "🔙 Back", "callback_data": "start_back"}],
    ]


def kb_thumb_menu() -> list[list[dict]]:
    return [
        [
            {"text": "👁️ View",   "callback_data": "thumb_view"},
            {"text": "🗑️ Delete", "callback_data": "thumb_del"},
        ],
        [{"text": "🔙 Back", "callback_data": "settings"}],
    ]
