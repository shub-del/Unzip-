"""
╔══════════════════════════════════════════════════════════╗
║           UNZIP BOT — database/mongo.py                  ║
║  Async MongoDB helpers via Motor.                        ║
╚══════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import time
from typing import Any

import motor.motor_asyncio
from loguru import logger

from config import cfg

# ─── Motor Client ────────────────────────────────────────────────────────────────
_client: motor.motor_asyncio.AsyncIOMotorClient | None = None
_db:     motor.motor_asyncio.AsyncIOMotorDatabase | None = None


async def init_db() -> None:
    """Connect to MongoDB. Called once on bot startup."""
    global _client, _db
    _client = motor.motor_asyncio.AsyncIOMotorClient(cfg.MONGO_URI)
    _db = _client[cfg.DB_NAME]
    # Ensure indexes
    await _db.users.create_index("user_id", unique=True)
    await _db.queue.create_index("user_id")
    await _db.queue.create_index("created_at")
    logger.info("MongoDB connected — DB: {}", cfg.DB_NAME)


def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _db


# ─── User Helpers ────────────────────────────────────────────────────────────────

async def get_user(user_id: int) -> dict[str, Any]:
    """Return user doc, creating a default one if absent."""
    db = get_db()
    doc = await db.users.find_one({"user_id": user_id})
    if doc is None:
        doc = _default_user(user_id)
        await db.users.insert_one(doc)
    return doc


def _default_user(user_id: int) -> dict[str, Any]:
    return {
        "user_id":   user_id,
        "premium":   False,
        "banned":    False,
        "lang":      cfg.DEFAULT_LANG,
        "mode":      "document",       # "document" | "media"
        "thumbnail": None,             # file_id of custom thumb
        "joined_at": int(time.time()),
        "extractions": 0,
        "bytes_extracted": 0,
    }


async def update_user(user_id: int, data: dict[str, Any]) -> None:
    db = get_db()
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": data},
        upsert=True,
    )


async def increment_stats(user_id: int, bytes_extracted: int) -> None:
    db = get_db()
    await db.users.update_one(
        {"user_id": user_id},
        {"$inc": {"extractions": 1, "bytes_extracted": bytes_extracted}},
        upsert=True,
    )


async def is_banned(user_id: int) -> bool:
    db = get_db()
    doc = await db.users.find_one({"user_id": user_id}, {"banned": 1})
    return bool(doc and doc.get("banned"))


async def is_premium(user_id: int) -> bool:
    if user_id == cfg.OWNER_ID or user_id in cfg.ADMIN_IDS:
        return True
    db = get_db()
    doc = await db.users.find_one({"user_id": user_id}, {"premium": 1})
    return bool(doc and doc.get("premium"))


async def set_premium(user_id: int, value: bool = True) -> None:
    await update_user(user_id, {"premium": value})


async def ban_user(user_id: int) -> None:
    await update_user(user_id, {"banned": True})


async def unban_user(user_id: int) -> None:
    await update_user(user_id, {"banned": False})


async def set_thumbnail(user_id: int, file_id: str | None) -> None:
    await update_user(user_id, {"thumbnail": file_id})


async def set_mode(user_id: int, mode: str) -> None:
    """mode = 'document' | 'media'"""
    await update_user(user_id, {"mode": mode})


async def set_lang(user_id: int, lang: str) -> None:
    await update_user(user_id, {"lang": lang})


# ─── Global Stats ────────────────────────────────────────────────────────────────

async def total_users() -> int:
    db = get_db()
    return await db.users.count_documents({})


async def total_premium() -> int:
    db = get_db()
    return await db.users.count_documents({"premium": True})


async def global_stats() -> dict[str, Any]:
    db = get_db()
    pipeline = [
        {"$group": {
            "_id":             None,
            "total_users":     {"$sum": 1},
            "premium_users":   {"$sum": {"$cond": ["$premium", 1, 0]}},
            "total_extractions": {"$sum": "$extractions"},
            "total_bytes":     {"$sum": "$bytes_extracted"},
        }}
    ]
    cursor = db.users.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    return result[0] if result else {}


# ─── Queue Helpers ────────────────────────────────────────────────────────────────

async def enqueue(user_id: int, task_data: dict[str, Any]) -> str:
    """Insert a task and return its inserted id as string."""
    db = get_db()
    doc = {"user_id": user_id, "created_at": int(time.time()), **task_data}
    result = await db.queue.insert_one(doc)
    return str(result.inserted_id)


async def dequeue(task_id: str) -> None:
    from bson import ObjectId
    db = get_db()
    await db.queue.delete_one({"_id": ObjectId(task_id)})


async def user_queue_size(user_id: int) -> int:
    db = get_db()
    return await db.queue.count_documents({"user_id": user_id})
