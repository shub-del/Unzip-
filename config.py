"""
╔══════════════════════════════════════════════════════════╗
║           UNZIP BOT — config.py                          ║
║  All configuration loaded from environment variables.    ║
║  Copy .env.example → .env and fill in your values.      ║
╚══════════════════════════════════════════════════════════╝
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ─── Telegram Credentials ───────────────────────────────────────────────────
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")          # @BotFather token
    API_ID: int    = int(os.environ.get("API_ID", "0"))        # my.telegram.org
    API_HASH: str  = os.environ.get("API_HASH", "")           # my.telegram.org

    # ─── Owner & Admins ─────────────────────────────────────────────────────────
    OWNER_ID: int           = int(os.environ.get("OWNER_ID", "0"))
    ADMIN_IDS: list[int]    = [
        int(x) for x in os.environ.get("ADMIN_IDS", "").split()
        if x.strip().lstrip("-").isdigit()
    ]

    # ─── MongoDB ────────────────────────────────────────────────────────────────
    MONGO_URI: str   = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME: str     = os.environ.get("DB_NAME", "unzip_bot")

    # ─── Force Subscribe ────────────────────────────────────────────────────────
    FORCE_SUB_CHANNEL: str | None = os.environ.get("FORCE_SUB_CHANNEL")  # e.g. "@mychannel"
    FORCE_SUB_ID: int | None = (
        int(os.environ.get("FORCE_SUB_ID", "0")) or None
    )

    # ─── Paths ──────────────────────────────────────────────────────────────────
    DOWNLOAD_DIR: str  = os.environ.get("DOWNLOAD_DIR", "./downloads")
    EXTRACT_DIR: str   = os.environ.get("EXTRACT_DIR",  "./extracted")
    THUMB_DIR: str     = os.environ.get("THUMB_DIR",    "./thumbnails")

    # ─── Limits ─────────────────────────────────────────────────────────────────
    MAX_FILE_SIZE: int      = int(os.environ.get("MAX_FILE_SIZE",    "2147483648"))  # 2 GB
    PREMIUM_MAX_SIZE: int   = int(os.environ.get("PREMIUM_MAX_SIZE", "4294967296"))  # 4 GB
    MAX_QUEUE_SIZE: int     = int(os.environ.get("MAX_QUEUE_SIZE", "5"))
    PROGRESS_UPDATE_SECS: float = float(os.environ.get("PROGRESS_UPDATE_SECS", "3"))

    # ─── Supported Archive Formats ──────────────────────────────────────────────
    SUPPORTED_EXTENSIONS: tuple[str, ...] = (
        ".zip", ".rar", ".7z",
        ".tar", ".tar.gz", ".tgz",
        ".tar.bz2", ".tbz2",
        ".tar.xz", ".txz",
        ".gz", ".bz2", ".xz",
    )

    # ─── Auto-delete after upload ───────────────────────────────────────────────
    AUTO_DELETE_SECS: int = int(os.environ.get("AUTO_DELETE_SECS", "60"))

    # ─── Premium Settings ───────────────────────────────────────────────────────
    PREMIUM_PASS: str = os.environ.get("PREMIUM_PASS", "changeme123")

    # ─── Logging ────────────────────────────────────────────────────────────────
    LOG_CHANNEL: int | None = (
        int(os.environ.get("LOG_CHANNEL", "0")) or None
    )

    # ─── Default Language ───────────────────────────────────────────────────────
    DEFAULT_LANG: str = os.environ.get("DEFAULT_LANG", "en")


cfg = Config()
