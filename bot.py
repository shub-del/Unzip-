import os
import logging
import asyncio
import zipfile
import rarfile
import tarfile
import py7zr
import shutil
import time
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

# ─── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "")
OWNER_ID    = int(os.environ.get("OWNER_ID", "0"))
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# ─── Helpers ───────────────────────────────────────────────────────────────────

def sizeof_fmt(num: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


def user_dir(user_id: int) -> Path:
    d = DOWNLOAD_DIR / str(user_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def clean_user_dir(user_id: int):
    d = DOWNLOAD_DIR / str(user_id)
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True, exist_ok=True)


async def edit_or_send(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs):
    """Edit current message if possible, otherwise send new."""
    msg = context.user_data.get("status_msg")
    try:
        if msg:
            await msg.edit_text(text, parse_mode=ParseMode.HTML, **kwargs)
            return msg
    except Exception:
        pass
    sent = await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML, **kwargs)
    context.user_data["status_msg"] = sent
    return sent


# ─── Commands ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ <b>Unzip Bot</b> — Active!\n\n"
        "📦 Mujhe koi <b>.zip / .rar / .7z / .tar.gz</b> file bhejo aur main usse extract kar ke wapas bhejunga!\n\n"
        "🔒 Password-protected archives bhi supported hain.\n"
        "Use /help for full command list.",
        parse_mode=ParseMode.HTML,
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>📋 Commands:</b>\n\n"
        "🚀 /start — Bot start karo\n"
        "❓ /help — Yeh message\n"
        "⭕ /status — Account status\n"
        "🚫 /cancel — Current process cancel karo\n"
        "🧹 /clean — Downloaded files clean karo\n"
        "✅ /done — Extraction finish karo\n"
        "📤 /mode — Upload mode set karo\n"
        "🌐 /lang — Language set karo\n\n"
        "<b>Supported formats:</b> .zip .rar .7z .tar .tar.gz .tar.bz2 .tar.xz",
        parse_mode=ParseMode.HTML,
    )


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    mode = context.user_data.get("upload_mode", "document")
    lang = context.user_data.get("lang", "auto")
    await update.message.reply_text(
        f"<b>👤 Account Status</b>\n\n"
        f"🆔 User ID: <code>{user.id}</code>\n"
        f"👤 Name: {user.full_name}\n"
        f"📤 Upload Mode: <b>{mode}</b>\n"
        f"🌐 Language: <b>{lang}</b>",
        parse_mode=ParseMode.HTML,
    )


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cancel"] = True
    await update.message.reply_text("🚫 Process cancel kar diya gaya.")


async def clean_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clean_user_dir(update.effective_user.id)
    await update.message.reply_text("🧹 Aapki saari downloaded files delete ho gayi!")


async def done_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clean_user_dir(update.effective_user.id)
    context.user_data.clear()
    await update.message.reply_text("✅ Session khatam! Naya archive bhejne ke liye taiyaar hoon.")


async def mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📄 Document", callback_data="mode_document"),
            InlineKeyboardButton("🎬 Media", callback_data="mode_media"),
        ]
    ]
    await update.message.reply_text(
        "📤 <b>Upload mode select karo:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML,
    )


async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🇮🇳 Hindi", callback_data="lang_hi"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ]
    ]
    await update.message.reply_text(
        "🌐 <b>Language select karo:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML,
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("mode_"):
        mode = data.split("_", 1)[1]
        context.user_data["upload_mode"] = mode
        await query.edit_message_text(f"✅ Upload mode set: <b>{mode}</b>", parse_mode=ParseMode.HTML)

    elif data.startswith("lang_"):
        lang = data.split("_", 1)[1]
        context.user_data["lang"] = lang
        label = "Hindi 🇮🇳" if lang == "hi" else "English 🇬🇧"
        await query.edit_message_text(f"✅ Language set: <b>{label}</b>", parse_mode=ParseMode.HTML)

    elif data == "cancel_extract":
        context.user_data["cancel"] = True
        await query.edit_message_text("🚫 Extraction cancel kar diya.")

    elif data.startswith("pass_"):
        # password prompt triggered via inline
        context.user_data["awaiting_password"] = True
        await query.edit_message_text(
            "🔑 Archive ka <b>password</b> bhejo (text message mein):",
            parse_mode=ParseMode.HTML,
        )


# ─── Archive Handling ──────────────────────────────────────────────────────────

SUPPORTED_EXTS = {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"}


def detect_format(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".tar.gz") or name.endswith(".tgz"):
        return "tar.gz"
    if name.endswith(".tar.bz2"):
        return "tar.bz2"
    if name.endswith(".tar.xz"):
        return "tar.xz"
    return path.suffix.lstrip(".")


def extract_archive(archive_path: Path, dest: Path, password: str = None) -> list[Path]:
    fmt = detect_format(archive_path)
    pwd_bytes = password.encode() if password else None

    if fmt == "zip":
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(dest, pwd=pwd_bytes)
    elif fmt == "rar":
        with rarfile.RarFile(archive_path) as rf:
            rf.extractall(dest, pwd=password)
    elif fmt == "7z":
        with py7zr.SevenZipFile(archive_path, mode="r", password=password) as sz:
            sz.extractall(dest)
    elif fmt in ("tar.gz", "tar.bz2", "tar.xz", "tar"):
        with tarfile.open(archive_path) as tf:
            tf.extractall(dest)
    else:
        raise ValueError(f"Unsupported format: {fmt}")

    files = [p for p in dest.rglob("*") if p.is_file()]
    return files


# ─── File Message Handler ──────────────────────────────────────────────────────

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user_id = update.effective_user.id

    # Get file object
    doc = message.document
    if doc is None:
        await message.reply_text("⚠️ Sirf archive files bhejo (.zip .rar .7z .tar.gz etc.)")
        return

    file_name = doc.file_name or "archive"
    ext = Path(file_name).suffix.lower()

    # Multi-part: .zip.001 / .part1.rar etc
    multi_part = file_name.lower().endswith((".001", ".part1.rar", ".part01.rar"))
    is_archive = (ext in SUPPORTED_EXTS) or multi_part

    if not is_archive:
        await message.reply_text(
            f"❌ <b>Unsupported file type:</b> <code>{ext}</code>\n\n"
            "Supported: .zip .rar .7z .tar .tar.gz .tar.bz2 .tar.xz",
            parse_mode=ParseMode.HTML,
        )
        return

    context.user_data["cancel"] = False

    # Status message
    status = await message.reply_text(
        f"⬇️ <b>Downloading:</b> <code>{file_name}</code>\n📦 Size: {sizeof_fmt(doc.file_size)}",
        parse_mode=ParseMode.HTML,
    )
    context.user_data["status_msg"] = status

    # Download
    udir = user_dir(user_id)
    dl_path = udir / file_name

    try:
        tg_file = await doc.get_file()
        start_time = time.time()
        await tg_file.download_to_drive(dl_path)
        elapsed = time.time() - start_time
        speed = doc.file_size / elapsed if elapsed > 0 else 0
    except Exception as e:
        await status.edit_text(f"❌ <b>Download Failed!</b>\n<code>{e}</code>", parse_mode=ParseMode.HTML)
        return

    await status.edit_text(
        f"✅ <b>Downloaded!</b> {sizeof_fmt(doc.file_size)} in {elapsed:.1f}s\n"
        f"⚡ Speed: {sizeof_fmt(speed)}/s\n\n"
        f"🔓 <b>Extracting...</b>",
        parse_mode=ParseMode.HTML,
    )

    # Try extract (no password first)
    extract_dir = udir / "extracted"
    extract_dir.mkdir(exist_ok=True)

    password = context.user_data.get("password")

    try:
        files = extract_archive(dl_path, extract_dir, password)
    except (RuntimeError, rarfile.BadRarFile, py7zr.exceptions.Bad7zFile) as e:
        if "password" in str(e).lower() or "encrypted" in str(e).lower():
            keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_extract")]]
            await status.edit_text(
                "🔒 <b>Archive is password protected!</b>\n\n"
                "🔑 Neeche <b>password</b> text karke bhejo:",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            context.user_data["awaiting_password"] = True
            context.user_data["archive_path"] = str(dl_path)
            context.user_data["extract_dir"] = str(extract_dir)
            return
        else:
            await status.edit_text(
                f"❌ <b>Extraction Failed!</b>\n\n"
                f"📝 <b>Check:</b>\n"
                f"• Archive not corrupted\n"
                f"• Correct password\n\n"
                f"<code>{e}</code>",
                parse_mode=ParseMode.HTML,
            )
            return
    except Exception as e:
        await status.edit_text(
            f"❌ <b>Extraction Failed!</b>\n\n"
            f"📝 <b>Check:</b>\n"
            f"• Archive not corrupted\n"
            f"• Correct password\n\n"
            f"<code>{e}</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    await upload_files(update, context, files, status)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle password input."""
    if not context.user_data.get("awaiting_password"):
        return

    password = update.message.text.strip()
    context.user_data["password"] = password
    context.user_data["awaiting_password"] = False

    archive_path = Path(context.user_data.get("archive_path", ""))
    extract_dir = Path(context.user_data.get("extract_dir", ""))

    if not archive_path.exists():
        await update.message.reply_text("❌ Archive file nahi mili. Dobara bhejo.")
        return

    status = await update.message.reply_text("🔑 Password mila! Extract kar raha hoon...", parse_mode=ParseMode.HTML)
    context.user_data["status_msg"] = status

    try:
        files = extract_archive(archive_path, extract_dir, password)
    except Exception as e:
        await status.edit_text(
            f"❌ <b>Extraction Failed!</b>\n\n"
            f"📝 <b>Check:</b>\n"
            f"• Archive not corrupted\n"
            f"• Correct password\n\n"
            f"<code>{e}</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    await upload_files(update, context, files, status)


async def upload_files(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    files: list[Path],
    status_msg,
):
    if not files:
        await status_msg.edit_text("⚠️ Archive empty hai ya extract nahi ho saka.")
        return

    mode = context.user_data.get("upload_mode", "document")
    total = len(files)
    total_size = sum(f.stat().st_size for f in files)

    await status_msg.edit_text(
        f"📤 <b>Uploading {total} file(s)...</b>\n"
        f"💾 Total size: {sizeof_fmt(total_size)}",
        parse_mode=ParseMode.HTML,
    )

    VIDEO_EXTS  = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
    IMAGE_EXTS  = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    for i, fpath in enumerate(files, 1):
        if context.user_data.get("cancel"):
            await status_msg.edit_text("🚫 Upload cancel kar diya gaya.")
            return

        caption = f"📁 <code>{fpath.name}</code>\n💾 {sizeof_fmt(fpath.stat().st_size)}"
        try:
            with open(fpath, "rb") as f:
                ext = fpath.suffix.lower()
                if mode == "media" and ext in VIDEO_EXTS:
                    await update.effective_message.reply_video(
                        f, caption=caption, parse_mode=ParseMode.HTML
                    )
                elif mode == "media" and ext in IMAGE_EXTS:
                    await update.effective_message.reply_photo(
                        f, caption=caption, parse_mode=ParseMode.HTML
                    )
                else:
                    await update.effective_message.reply_document(
                        f, caption=caption, parse_mode=ParseMode.HTML
                    )
        except Exception as e:
            await update.effective_message.reply_text(
                f"⚠️ <code>{fpath.name}</code> upload nahi hua: <code>{e}</code>",
                parse_mode=ParseMode.HTML,
            )

        if total > 1:
            await status_msg.edit_text(
                f"📤 Uploading... ({i}/{total})\n"
                f"📁 <code>{fpath.name}</code>",
                parse_mode=ParseMode.HTML,
            )

    await status_msg.edit_text(
        f"✅ <b>Successfully extracted & uploaded!</b>\n"
        f"📦 {total} file(s) • {sizeof_fmt(total_size)}\n\n"
        f"🧹 Files clean karne ke liye /clean\n"
        f"✅ Session khatam karne ke liye /done",
        parse_mode=ParseMode.HTML,
    )


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable set nahi hai!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("help",   help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(CommandHandler("clean",  clean_cmd))
    app.add_handler(CommandHandler("done",   done_cmd))
    app.add_handler(CommandHandler("mode",   mode_cmd))
    app.add_handler(CommandHandler("lang",   lang_cmd))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot start ho gaya! 🚀")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
