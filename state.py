"""
╔══════════════════════════════════════════════════════════╗
║           UNZIP BOT — handlers/state.py                  ║
║  In-memory per-user task state.                          ║
╚══════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TaskState:
    """Tracks one active extraction job for a user."""
    user_id:    int
    filename:   str
    work_dir:   str
    stage:      str       = "idle"       # idle | downloading | extracting | uploading
    percent:    int       = 0
    started_at: float     = field(default_factory=time.monotonic)
    cancelled:  bool      = False
    password:   Optional[str] = None


# Global registry: user_id → TaskState
task_registry: dict[int, TaskState] = {}


# Passwords awaiting input: user_id → asyncio.Future
pending_passwords: dict[int, "asyncio.Future[str | None]"] = {}
