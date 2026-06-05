"""
╔══════════════════════════════════════════════════════════╗
║           UNZIP BOT — handlers/archive.py                ║
║  Handles incoming archive files end-to-end:              ║
║    download → password? → extract → upload → cleanup     ║
╚══════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

from loguru import logger
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import cfg
from database import (
    get_user, is_banned, is_premium,
    increment_stats, user_queue_size,
)
from locales.strings import get_string
from utils import (
    fmt_size, fmt_speed, fmt_elapsed, fmt_eta,
    make_progress_bar, ensure_dirs, safe_remove, auto_delete,
    dir_size, list_files_recursive,
    get_archive_type, archive_needs_password,
    extract_archive,
    CorruptArchiveError, WrongPasswordError, UnsupportedFormatError,
    kb_cancel,
)
from handlers.state import task_registry, pending_passwords, TaskState


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _kb(rows: list[list[dict]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(**btn) for btn in row] for row in rows]
    )


async def _safe_edit(msg: Message, text: str, **kwargs) -> None:
    """Edit message, handling FloodWait gracefully."""
    try:
        await msg.edit_text(text, **kwargs)
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception:
        pass


# ─── Gate-checks ─────────────────────────────────────────────────────────────

async def _check_gates(client: Client, msg: Message, uid: int) -> bool:
    """Return True if user may proceed. Sends error message otherwise."""
    if await is_banned(uid):
        user = await get_user(uid)
        await msg.reply(get_string(user.get("lang", "en"), "banned"))
        return False

    # Force subscribe
    if cfg.FORCE_SUB_ID:
        try:
            member = await client.get_chat_member(cfg.FORCE_SUB_ID, uid)
            if member.status.value in ("left", "kicked"):
                raise Exception
        except Exception:
            chat = await client.get_chat(cfg.FORCE_SUB_ID)
            link = getattr(chat, "invite_link", cfg.FORCE_SUB_CHANNEL) or ""
            user = await get_user(uid)
            lang = user.get("lang", "en")
            await msg.reply(
                get_string(lang, "force_sub", channel=cfg.FORCE_SUB_CHANNEL),
                reply_markup=_kb(
                    [[{"text": "📢 Join Channel", "url": link}],
                     [{"text": "✅ Joined", "callback_data": "check_sub"}]]
                ),
            )
            return False

    return True


# ─── Progress Callback Builder ───────────────────────────────────────────────

def _build_progress(
    status_msg: Message,
    template_key: str,
    lang: str,
    filename: str,
    task: TaskState,
    stage: str,
) -> callable:
    """Return an async progress callback for Pyrogram upload/download."""
    last_call: list[float] = [0.0]
    start_time: list[float] = [time.monotonic()]

    async def progress(current: int, total: int) -> None:
        if task.cancelled:
            return
        now = time.monotonic()
        if now - last_call[0] < cfg.PROGRESS_UPDATE_SECS and current < total:
            return
        last_call[0] = now

        elapsed   = now - start_time[0]
        speed     = current / elapsed if elapsed > 0 else 0
        remaining = total - current
        percent   = int(current / total * 100) if total else 0
        bar       = make_progress_bar(percent)

        task.percent = percent
        task.stage   = stage

        text = get_string(
            lang, template_key,
            name=filename,
            bar=bar,
            percent=percent,
            done=fmt_size(current),
            total=fmt_size(total),
            speed=fmt_speed(speed),
            eta=fmt_eta(remaining, speed),
        )
        await _safe_edit(status_msg, text, reply_markup=_kb(kb_cancel()))

    return progress


# ─── Main File Handler ────────────────────────────────────────────────────────

@Client.on_message(
    filters.private
    & (filters.document | filters.audio | filters.video | filters.photo)
)
async def handle_archive(client: Client, msg: Message) -> None:
    uid = msg.from_user.id

    # Ignore messages without a document (e.g. photos not meant as archives)
    doc = msg.document
    if doc is None:
        return

    if not await _check_gates(client, msg, uid):
        return

    user = await get_user(uid)
    lang = user.get("lang", cfg.DEFAULT_LANG)
    name = doc.file_name or "archive"

    # ── Validate format ──────────────────────────────────────────────────────
    if get_archive_type(name) is None:
        await msg.reply(get_string(lang, "unsupported"))
        return

    # ── File size guard ──────────────────────────────────────────────────────
    premium = await is_premium(uid)
    max_size = cfg.PREMIUM_MAX_SIZE if premium else cfg.MAX_FILE_SIZE
    if doc.file_size and doc.file_size > max_size:
        await msg.reply(
            get_string(lang, "too_large",
                       max=fmt_size(max_size),
                       size=fmt_size(doc.file_size))
        )
        return

    # ── Queue guard ──────────────────────────────────────────────────────────
    if uid in task_registry:
        q = await user_queue_size(uid)
        if q >= cfg.MAX_QUEUE_SIZE:
            await msg.reply(get_string(lang, "queue_full", max=cfg.MAX_QUEUE_SIZE))
            return
        await msg.reply(get_string(lang, "wait_queue", n=q))
        return

    # ── Prepare work directories ─────────────────────────────────────────────
    work_base   = Path(cfg.DOWNLOAD_DIR) / str(uid)
    extract_dir = Path(cfg.EXTRACT_DIR) / str(uid) / str(int(time.time()))
    ensure_dirs(str(work_base), str(extract_dir))

    archive_path = str(work_base / name)

    # ── Register task ────────────────────────────────────────────────────────
    task = TaskState(user_id=uid, filename=name, work_dir=str(work_base))
    task_registry[uid] = task

    # ── Status message ───────────────────────────────────────────────────────
    status_msg = await msg.reply(
        f"⏳ Preparing…",
        reply_markup=_kb(kb_cancel()),
    )

    try:
        # ── DOWNLOAD ─────────────────────────────────────────────────────────
        task.stage = "downloading"
        dl_cb = _build_progress(status_msg, "downloading", lang, name, task, "downloading")

        await client.download_media(
            msg,
            file_name=archive_path,
            progress=dl_cb,
        )

        if task.cancelled:
            return

        # ── PASSWORD CHECK ────────────────────────────────────────────────────
        password: str | None = None
        if archive_needs_password(archive_path):
            fut: asyncio.Future[str | None] = asyncio.get_event_loop().create_future()
            pending_passwords[uid] = fut

            await _safe_edit(
                status_msg,
                get_string(lang, "ask_password"),
                reply_markup=_kb([[{"text": "🛑 Cancel", "callback_data": "cancel_task"}]]),
            )

            try:
                # Wait up to 5 minutes for the user to reply
                password = await asyncio.wait_for(fut, timeout=300)
            except asyncio.TimeoutError:
                password = None
            finally:
                pending_passwords.pop(uid, None)

            if task.cancelled or password is None:
                await _safe_edit(status_msg, get_string(lang, "cancelled"))
                return

        # ── EXTRACT ───────────────────────────────────────────────────────────
        task.stage = "extracting"
        await _safe_edit(
            status_msg,
            get_string(lang, "extracting", name=name, bar=make_progress_bar(0), percent=0),
            reply_markup=_kb(kb_cancel()),
        )

        try:
            extracted_files = await extract_archive(archive_path, str(extract_dir), password)
        except WrongPasswordError:
            await _safe_edit(status_msg, get_string(lang, "wrong_password"))
            return
        except CorruptArchiveError as exc:
            await _safe_edit(status_msg, get_string(lang, "corrupt", error=str(exc)[:200]))
            return
        except UnsupportedFormatError:
            await _safe_edit(status_msg, get_string(lang, "unsupported"))
            return

        if task.cancelled:
            return

        total_bytes = dir_size(str(extract_dir))
        file_count  = len(extracted_files)

        await _safe_edit(
            status_msg,
            get_string(lang, "extract_done",
                       count=file_count, size=fmt_size(total_bytes)),
        )

        if task.cancelled:
            return

        # ── UPLOAD ────────────────────────────────────────────────────────────
        task.stage = "uploading"
        mode  = user.get("mode", "document")
        thumb = user.get("thumbnail")

        for i, file_path in enumerate(extracted_files, 1):
            if task.cancelled:
                break

            fname = file_path.name
            fsize = file_path.stat().st_size

            upload_status = await msg.reply(
                f"⬆️ Uploading [{i}/{file_count}]: **{fname}**",
                reply_markup=_kb(kb_cancel()),
            )
            up_cb = _build_progress(upload_status, "uploading", lang, fname, task, "uploading")

            try:
                if _is_video(fname) and mode == "media":
                    await client.send_video(
                        msg.chat.id,
                        str(file_path),
                        caption=f"🎬 `{fname}`  •  {fmt_size(fsize)}",
                        thumb=thumb,
                        progress=up_cb,
                        reply_to_message_id=msg.id,
                    )
                elif _is_audio(fname) and mode == "media":
                    await client.send_audio(
                        msg.chat.id,
                        str(file_path),
                        caption=f"🎵 `{fname}`  •  {fmt_size(fsize)}",
                        thumb=thumb,
                        progress=up_cb,
                        reply_to_message_id=msg.id,
                    )
                else:
                    await client.send_document(
                        msg.chat.id,
                        str(file_path),
                        caption=f"📄 `{fname}`  •  {fmt_size(fsize)}",
                        thumb=thumb,
                        progress=up_cb,
                        reply_to_message_id=msg.id,
                    )
                await upload_status.delete()
            except Exception as exc:
                logger.error("Upload failed {}: {}", fname, exc)
                await _safe_edit(upload_status, get_string(lang, "error_generic", error=str(exc)[:200]))

        # ── DONE ─────────────────────────────────────────────────────────────
        elapsed = fmt_elapsed(time.monotonic() - task.started_at)
        await _safe_edit(
            status_msg,
            get_string(
                lang, "all_done",
                count=file_count,
                archive=name,
                size=fmt_size(total_bytes),
                time=elapsed,
                del_secs=cfg.AUTO_DELETE_SECS,
            ),
        )

        # ── Stats ─────────────────────────────────────────────────────────────
        await increment_stats(uid, total_bytes)

        # ── Log to channel ────────────────────────────────────────────────────
        if cfg.LOG_CHANNEL:
            try:
                await client.send_message(
                    cfg.LOG_CHANNEL,
                    f"✅ **Extraction**\n"
                    f"👤 User: [{msg.from_user.first_name}](tg://user?id={uid}) `{uid}`\n"
                    f"📦 Archive: `{name}`\n"
                    f"📂 Files: {file_count}  •  {fmt_size(total_bytes)}\n"
                    f"⏱ Time: {elapsed}",
                )
            except Exception:
                pass

    except asyncio.CancelledError:
        await _safe_edit(status_msg, get_string(lang, "cancelled"))
    except Exception as exc:
        logger.exception("Unhandled error for user {}: {}", uid, exc)
        await _safe_edit(status_msg, get_string(lang, "error_generic", error=str(exc)[:200]))
    finally:
        task_registry.pop(uid, None)
        # Auto-clean work dirs
        asyncio.create_task(auto_delete(work_base,   cfg.AUTO_DELETE_SECS))
        asyncio.create_task(auto_delete(extract_dir, cfg.AUTO_DELETE_SECS))


# ─── Password Reply Listener ──────────────────────────────────────────────────

@Client.on_message(filters.private & filters.text & ~filters.command(["cancel", "start", "help"]))
async def handle_text(client: Client, msg: Message) -> None:
    uid = msg.from_user.id

    # If we're waiting for a password from this user, resolve the future
    if uid in pending_passwords:
        fut = pending_passwords.pop(uid, None)
        if fut and not fut.done():
            fut.set_result(msg.text.strip())
        try:
            await msg.delete()
        except Exception:
            pass


# ─── Format helpers ───────────────────────────────────────────────────────────

_VIDEO_EXTS  = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv"}
_AUDIO_EXTS  = {".mp3", ".flac", ".ogg", ".m4a", ".wav", ".aac", ".opus"}

def _is_video(filename: str) -> bool:
    return Path(filename).suffix.lower() in _VIDEO_EXTS

def _is_audio(filename: str) -> bool:
    return Path(filename).suffix.lower() in _AUDIO_EXTS
