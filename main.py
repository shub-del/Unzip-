"""
╔══════════════════════════════════════════════════════════╗
║           UNZIP BOT — main.py                            ║
║  Entry point: initialise DB, create dirs, start bot.     ║
╚══════════════════════════════════════════════════════════╝

Usage:
    python main.py

Environment:
    Copy .env.example → .env and fill in your credentials.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from loguru import logger
from pyrogram import Client, idle

from config import cfg
from database import init_db
from utils import ensure_dirs

# ─── Import all handler modules so decorators register ───────────────────────
import handlers  # noqa: F401  (side-effect imports)


# ─── Logging ─────────────────────────────────────────────────────────────────
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> — <level>{message}</level>",
    level="INFO",
    colorize=True,
)
logger.add(
    "logs/bot.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    enqueue=True,
)


# ─── Validation ──────────────────────────────────────────────────────────────
def _validate_config() -> None:
    missing = []
    if not cfg.BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not cfg.API_ID:
        missing.append("API_ID")
    if not cfg.API_HASH:
        missing.append("API_HASH")
    if missing:
        logger.error("Missing required config: {}", ", ".join(missing))
        sys.exit(1)


# ─── App ─────────────────────────────────────────────────────────────────────
def create_app() -> Client:
    return Client(
        name="unzip_bot",
        api_id=cfg.API_ID,
        api_hash=cfg.API_HASH,
        bot_token=cfg.BOT_TOKEN,
        workers=4,                    # Parallel handler workers
        sleep_threshold=30,           # Auto-sleep on FloodWait < 30s
    )


# ─── Startup / Shutdown ───────────────────────────────────────────────────────
async def main() -> None:
    _validate_config()

    # Create working directories
    ensure_dirs(
        cfg.DOWNLOAD_DIR,
        cfg.EXTRACT_DIR,
        cfg.THUMB_DIR,
        "logs",
    )

    # Connect to MongoDB
    await init_db()

    # Start Pyrogram
    app = create_app()
    await app.start()

    me = await app.get_me()
    logger.info("Bot started: @{} ({})", me.username, me.id)

    if cfg.LOG_CHANNEL:
        try:
            await app.send_message(
                cfg.LOG_CHANNEL,
                f"🤖 **UnZip Bot started**\n@{me.username}",
            )
        except Exception as exc:
            logger.warning("Could not notify log channel: {}", exc)

    await idle()

    logger.info("Shutting down…")
    await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
