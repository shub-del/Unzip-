"""
╔══════════════════════════════════════════════════════════╗
║           UNZIP BOT — handlers/commands.py               ║
║  All slash-command handlers.                             ║
╚══════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from loguru import logger
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import cfg
from database import (
    get_user, is_banned, is_premium,
    set_thumbnail, global_stats,
)
from locales.strings import get_string
from utils import (
    kb_start, kb_settings, kb_thumb_menu,
    fmt_size, fmt_elapsed, safe_remove, ensure_dirs,
)

# Shared per-user task registry  {user_id: TaskState}
from handlers.state import task_registry, TaskState


def _kb(rows: list[list[dict]]) -> InlineKeyboardMarkup:
    """Convert raw dict rows → Pyrogram InlineKeyboardMarkup."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(**btn) for btn in row] for row in rows]
    )


# ─── /start ──────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("start") & filters.private)
async def cmd_start(client: Client, msg: Message) -> None:
    if await is_banned(msg.from_user.id):
        await msg.reply(get_string("en", "banned"))
        return

    user = await get_user(msg.from_user.id)
    lang = user.get("lang", cfg.DEFAULT_LANG)

    # Force-subscribe check
    if cfg.FORCE_SUB_CHANNEL and cfg.FORCE_SUB_ID:
        try:
            member = await client.get_chat_member(cfg.FORCE_SUB_ID, msg.from_user.id)
            if member.status.value in ("left", "kicked"):
                raise Exception("not member")
        except Exception:
            chat = await client.get_chat(cfg.FORCE_SUB_ID)
            link = getattr(chat, "invite_link", cfg.FORCE_SUB_CHANNEL) or cfg.FORCE_SUB_CHANNEL
            await msg.reply(
                get_string(lang, "force_sub", channel=cfg.FORCE_SUB_CHANNEL),
                reply_markup=_kb(
                    [[{"text": "📢 Join Channel", "url": link}],
                     [{"text": "✅ Joined", "callback_data": "check_sub"}]]
                ),
            )
            return

    text = get_string(lang, "start", name=msg.from_user.first_name)
    await msg.reply(text, reply_markup=_kb(kb_start()), disable_web_page_preview=True)


# ─── /help ───────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("help") & filters.private)
async def cmd_help(client: Client, msg: Message) -> None:
    user = await get_user(msg.from_user.id)
    lang = user.get("lang", cfg.DEFAULT_LANG)
    await msg.reply(
        get_string(lang, "help"),
        reply_markup=_kb([[{"text": "🔙 Back", "callback_data": "start_back"}]]),
    )


# ─── /status ─────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("status") & filters.private)
async def cmd_status(client: Client, msg: Message) -> None:
    uid = msg.from_user.id
    user = await get_user(uid)
    lang = user.get("lang", cfg.DEFAULT_LANG)
    task = task_registry.get(uid)

    if task is None or task.stage == "idle":
        await msg.reply(get_string(lang, "status_idle"))
    else:
        import time
        elapsed = fmt_elapsed(time.monotonic() - task.started_at)
        await msg.reply(
            get_string(
                lang, "status_active",
                name=task.filename,
                stage=task.stage,
                percent=task.percent,
                elapsed=elapsed,
            )
        )


# ─── /cancel ─────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("cancel") & filters.private)
async def cmd_cancel(client: Client, msg: Message) -> None:
    uid = msg.from_user.id
    user = await get_user(uid)
    lang = user.get("lang", cfg.DEFAULT_LANG)
    task = task_registry.get(uid)

    if task is None:
        await msg.reply(get_string(lang, "no_active"))
        return

    task.cancelled = True
    task_registry.pop(uid, None)
    safe_remove(task.work_dir)
    await msg.reply(get_string(lang, "cancelled"))


# ─── /clean ──────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("clean") & filters.private)
async def cmd_clean(client: Client, msg: Message) -> None:
    uid = msg.from_user.id
    user = await get_user(uid)
    lang = user.get("lang", cfg.DEFAULT_LANG)

    # Remove user's download/extract directories
    for base in (cfg.DOWNLOAD_DIR, cfg.EXTRACT_DIR):
        user_dir = Path(base) / str(uid)
        safe_remove(user_dir)

    await msg.reply(get_string(lang, "cleaned"))


# ─── /done ───────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("done") & filters.private)
async def cmd_done(client: Client, msg: Message) -> None:
    await cmd_cancel(client, msg)   # alias — cancel + clean


# ─── /mode ───────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("mode") & filters.private)
async def cmd_mode(client: Client, msg: Message) -> None:
    user = await get_user(msg.from_user.id)
    from utils import kb_mode_select
    await msg.reply(
        "⚙️ **Select Upload Mode**",
        reply_markup=_kb(kb_mode_select(user.get("mode", "document"))),
    )


# ─── /lang ───────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("lang") & filters.private)
async def cmd_lang(client: Client, msg: Message) -> None:
    from utils import kb_lang_select
    await msg.reply("🌐 **Select Language**", reply_markup=_kb(kb_lang_select()))


# ─── /save (save thumbnail) ───────────────────────────────────────────────────

@Client.on_message(filters.command("save") & filters.private)
async def cmd_save(client: Client, msg: Message) -> None:
    uid  = msg.from_user.id
    user = await get_user(uid)
    lang = user.get("lang", cfg.DEFAULT_LANG)

    photo = msg.photo or (msg.reply_to_message and msg.reply_to_message.photo)
    if not photo:
        await msg.reply("🖼️ Send this command as a reply to a **photo** to save it as your thumbnail.")
        return

    file_id = photo.file_id
    await set_thumbnail(uid, file_id)
    await msg.reply(get_string(lang, "thumb_saved"))


# ─── /thget (view thumbnail) ─────────────────────────────────────────────────

@Client.on_message(filters.command("thget") & filters.private)
async def cmd_thget(client: Client, msg: Message) -> None:
    uid  = msg.from_user.id
    user = await get_user(uid)
    lang = user.get("lang", cfg.DEFAULT_LANG)
    thumb = user.get("thumbnail")

    if not thumb:
        await msg.reply(get_string(lang, "thumb_none"))
    else:
        await msg.reply_photo(thumb, caption="🖼️ Your current thumbnail.")


# ─── /thdel (delete thumbnail) ───────────────────────────────────────────────

@Client.on_message(filters.command("thdel") & filters.private)
async def cmd_thdel(client: Client, msg: Message) -> None:
    uid  = msg.from_user.id
    user = await get_user(uid)
    lang = user.get("lang", cfg.DEFAULT_LANG)
    await set_thumbnail(uid, None)
    await msg.reply(get_string(lang, "thumb_deleted"))


# ─── Admin: /ban /unban /addpremium /delpremium /broadcast /stats ─────────────

def _admin_filter(_, __, msg: Message) -> bool:
    return msg.from_user is not None and (
        msg.from_user.id == cfg.OWNER_ID or msg.from_user.id in cfg.ADMIN_IDS
    )

admin_only = filters.create(_admin_filter)


@Client.on_message(filters.command("ban") & admin_only)
async def cmd_ban(client: Client, msg: Message) -> None:
    from database import ban_user
    if len(msg.command) < 2:
        await msg.reply("Usage: /ban <user_id>"); return
    uid = int(msg.command[1])
    await ban_user(uid)
    await msg.reply(f"🔨 User `{uid}` banned.")


@Client.on_message(filters.command("unban") & admin_only)
async def cmd_unban(client: Client, msg: Message) -> None:
    from database import unban_user
    if len(msg.command) < 2:
        await msg.reply("Usage: /unban <user_id>"); return
    uid = int(msg.command[1])
    await unban_user(uid)
    await msg.reply(f"✅ User `{uid}` unbanned.")


@Client.on_message(filters.command("addpremium") & admin_only)
async def cmd_add_premium(client: Client, msg: Message) -> None:
    from database import set_premium
    if len(msg.command) < 2:
        await msg.reply("Usage: /addpremium <user_id>"); return
    uid = int(msg.command[1])
    await set_premium(uid, True)
    await msg.reply(f"👑 User `{uid}` upgraded to Premium.")


@Client.on_message(filters.command("delpremium") & admin_only)
async def cmd_del_premium(client: Client, msg: Message) -> None:
    from database import set_premium
    if len(msg.command) < 2:
        await msg.reply("Usage: /delpremium <user_id>"); return
    uid = int(msg.command[1])
    await set_premium(uid, False)
    await msg.reply(f"User `{uid}` downgraded from Premium.")


@Client.on_message(filters.command("stats") & admin_only)
async def cmd_stats(client: Client, msg: Message) -> None:
    s = await global_stats()
    text = (
        "📊 **Global Stats**\n"
        f"👥 Total users:    `{s.get('total_users', 0)}`\n"
        f"👑 Premium users:  `{s.get('premium_users', 0)}`\n"
        f"🗜️ Extractions:    `{s.get('total_extractions', 0)}`\n"
        f"💾 Data extracted: `{fmt_size(s.get('total_bytes', 0))}`"
    )
    await msg.reply(text)


@Client.on_message(filters.command("broadcast") & admin_only)
async def cmd_broadcast(client: Client, msg: Message) -> None:
    if not msg.reply_to_message:
        await msg.reply("Reply to a message to broadcast it."); return

    from database import get_db
    db = get_db()
    cursor = db.users.find({}, {"user_id": 1})
    sent = failed = 0
    async for doc in cursor:
        try:
            await msg.reply_to_message.copy(doc["user_id"])
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    await msg.reply(f"📡 Broadcast done.\n✅ Sent: {sent}  ❌ Failed: {failed}")
