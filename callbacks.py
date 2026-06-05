"""
╔══════════════════════════════════════════════════════════╗
║           UNZIP BOT — handlers/callbacks.py              ║
║  All inline-button callback_data handlers.               ║
╚══════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config import cfg
from database import (
    get_user, set_mode, set_lang, set_thumbnail, is_premium,
)
from locales.strings import get_string
from utils import (
    fmt_size, safe_remove,
    kb_start, kb_settings, kb_mode_select, kb_lang_select, kb_thumb_menu,
)
from handlers.state import task_registry


def _kb(rows: list[list[dict]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(**btn) for btn in row] for row in rows]
    )


@Client.on_callback_query()
async def handle_callback(client: Client, cq: CallbackQuery) -> None:
    uid  = cq.from_user.id
    data = cq.data or ""

    user = await get_user(uid)
    lang = user.get("lang", cfg.DEFAULT_LANG)

    # ── Force-sub check ───────────────────────────────────────────────────────
    if data == "check_sub":
        if cfg.FORCE_SUB_ID:
            try:
                member = await client.get_chat_member(cfg.FORCE_SUB_ID, uid)
                if member.status.value in ("left", "kicked"):
                    raise Exception
                await cq.answer("✅ Welcome!", show_alert=True)
                text = get_string(lang, "start", name=cq.from_user.first_name)
                await cq.message.edit_text(text, reply_markup=_kb(kb_start()))
            except Exception:
                await cq.answer("❌ You haven't joined yet!", show_alert=True)
        else:
            await cq.answer()
        return

    # ── Navigation ────────────────────────────────────────────────────────────
    if data == "start_back":
        text = get_string(lang, "start", name=cq.from_user.first_name)
        await cq.message.edit_text(text, reply_markup=_kb(kb_start()))
        await cq.answer()
        return

    if data == "help":
        await cq.message.edit_text(
            get_string(lang, "help"),
            reply_markup=_kb([[{"text": "🔙 Back", "callback_data": "start_back"}]]),
        )
        await cq.answer()
        return

    if data == "settings":
        await cq.message.edit_text(
            "⚙️ **Settings**\n\nChoose what you'd like to configure:",
            reply_markup=_kb(kb_settings()),
        )
        await cq.answer()
        return

    # ── Mode selection ────────────────────────────────────────────────────────
    if data == "choose_mode":
        current = user.get("mode", "document")
        await cq.message.edit_text(
            "📤 **Upload Mode**\n\n"
            "**Document** — Files sent as documents (always downloadable).\n"
            "**Media** — Videos/audio sent as streamable media.",
            reply_markup=_kb(kb_mode_select(current)),
        )
        await cq.answer()
        return

    if data in ("mode_document", "mode_media"):
        mode = data.split("_")[1]
        await set_mode(uid, mode)
        await cq.answer(f"✅ Mode set to {mode.title()}", show_alert=False)
        await cq.message.edit_reply_markup(reply_markup=_kb(kb_mode_select(mode)))
        return

    # ── Language selection ────────────────────────────────────────────────────
    if data == "choose_lang":
        await cq.message.edit_text(
            "🌐 **Select Language**",
            reply_markup=_kb(kb_lang_select()),
        )
        await cq.answer()
        return

    if data == "lang_en":
        await set_lang(uid, "en")
        await cq.answer("🇬🇧 Language set to English", show_alert=False)
        await cq.message.edit_text(
            get_string("en", "start", name=cq.from_user.first_name),
            reply_markup=_kb(kb_start()),
        )
        return

    if data == "lang_hi":
        await set_lang(uid, "hi")
        await cq.answer("🇮🇳 भाषा हिन्दी में बदली गई", show_alert=False)
        await cq.message.edit_text(
            get_string("hi", "start", name=cq.from_user.first_name),
            reply_markup=_kb(kb_start()),
        )
        return

    # ── Thumbnail menu ────────────────────────────────────────────────────────
    if data == "thumb_menu":
        await cq.message.edit_text(
            "🖼️ **Thumbnail**\n\nManage your custom thumbnail shown on uploaded files.",
            reply_markup=_kb(kb_thumb_menu()),
        )
        await cq.answer()
        return

    if data == "thumb_view":
        thumb = user.get("thumbnail")
        if not thumb:
            await cq.answer(get_string(lang, "thumb_none"), show_alert=True)
        else:
            await client.send_photo(cq.message.chat.id, thumb, caption="🖼️ Your current thumbnail.")
            await cq.answer()
        return

    if data == "thumb_del":
        await set_thumbnail(uid, None)
        await cq.answer(get_string(lang, "thumb_deleted"), show_alert=True)
        return

    # ── My Stats ─────────────────────────────────────────────────────────────
    if data == "my_stats":
        prem = await is_premium(uid)
        text = (
            f"📊 **Your Stats**\n\n"
            f"👤 ID: `{uid}`\n"
            f"👑 Premium: {'Yes ✅' if prem else 'No ❌'}\n"
            f"🗜️ Extractions: `{user.get('extractions', 0)}`\n"
            f"💾 Data extracted: `{fmt_size(user.get('bytes_extracted', 0))}`\n"
            f"🌐 Language: `{user.get('lang', 'en')}`\n"
            f"📤 Upload mode: `{user.get('mode', 'document')}`"
        )
        await cq.message.edit_text(text, reply_markup=_kb([[{"text": "🔙 Back", "callback_data": "start_back"}]]))
        await cq.answer()
        return

    # ── Premium info ─────────────────────────────────────────────────────────
    if data == "premium_info":
        await cq.message.edit_text(
            "👑 **Premium Plan**\n\n"
            "• Up to **4 GB** file size (vs 2 GB free)\n"
            "• Priority extraction queue\n"
            "• No wait times\n"
            "• All archive formats unlocked\n\n"
            "Contact the bot owner to upgrade.",
            reply_markup=_kb([[{"text": "🔙 Back", "callback_data": "start_back"}]]),
        )
        await cq.answer()
        return

    # ── Cancel active task ────────────────────────────────────────────────────
    if data == "cancel_task":
        task = task_registry.get(uid)
        if task:
            task.cancelled = True
            task_registry.pop(uid, None)
            safe_remove(task.work_dir)
            await cq.answer(get_string(lang, "cancelled"), show_alert=True)
            try:
                await cq.message.edit_text(get_string(lang, "cancelled"))
            except Exception:
                pass
        else:
            await cq.answer(get_string(lang, "no_active"), show_alert=True)
        return

    # ── Default ───────────────────────────────────────────────────────────────
    await cq.answer()
