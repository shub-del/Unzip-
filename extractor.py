"""
╔══════════════════════════════════════════════════════════╗
║           UNZIP BOT — utils/extractor.py                 ║
║  Async wrapper around patool / rarfile / py7zr.          ║
╚══════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import asyncio
import os
import zipfile
from pathlib import Path

import py7zr
import rarfile
from loguru import logger

from utils.helpers import list_files_recursive


# ─── Custom Exceptions ────────────────────────────────────────────────────────

class CorruptArchiveError(Exception):
    pass

class WrongPasswordError(Exception):
    pass

class UnsupportedFormatError(Exception):
    pass


# ─── Detection ────────────────────────────────────────────────────────────────

def _is_encrypted_zip(path: str) -> bool:
    try:
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                if info.flag_bits & 0x1:
                    return True
    except Exception:
        pass
    return False


def _is_encrypted_7z(path: str) -> bool:
    try:
        with py7zr.SevenZipFile(path) as zf:
            return zf.needs_password()
    except Exception:
        return False


def _is_encrypted_rar(path: str) -> bool:
    try:
        with rarfile.RarFile(path) as rf:
            return rf.needs_password()
    except Exception:
        return False


def archive_needs_password(path: str) -> bool:
    """Return True if archive is password-protected."""
    name = path.lower()
    if name.endswith(".zip"):
        return _is_encrypted_zip(path)
    if name.endswith(".7z"):
        return _is_encrypted_7z(path)
    if name.endswith(".rar"):
        return _is_encrypted_rar(path)
    return False


# ─── Async Extraction ─────────────────────────────────────────────────────────

async def extract_archive(
    archive_path: str,
    extract_to: str,
    password: str | None = None,
) -> list[Path]:
    """
    Extract archive to extract_to directory.
    Returns list of extracted file paths.
    Raises CorruptArchiveError | WrongPasswordError | UnsupportedFormatError.
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        _extract_sync,
        archive_path,
        extract_to,
        password,
    )
    return list_files_recursive(extract_to)


def _extract_sync(archive_path: str, extract_to: str, password: str | None) -> None:
    """Synchronous extraction — runs in a thread-pool executor."""
    os.makedirs(extract_to, exist_ok=True)
    name = archive_path.lower()

    try:
        if name.endswith(".zip") or name.endswith(".zip.001"):
            _extract_zip(archive_path, extract_to, password)

        elif name.endswith(".rar") or _is_rar_ext(name):
            _extract_rar(archive_path, extract_to, password)

        elif name.endswith(".7z"):
            _extract_7z(archive_path, extract_to, password)

        elif any(name.endswith(e) for e in (".tar", ".tar.gz", ".tgz",
                                             ".tar.bz2", ".tbz2",
                                             ".tar.xz", ".txz", ".gz", ".bz2", ".xz")):
            _extract_tar(archive_path, extract_to)

        else:
            # Fallback: patool handles many exotic formats
            _extract_patool(archive_path, extract_to, password)

    except (WrongPasswordError, CorruptArchiveError, UnsupportedFormatError):
        raise
    except Exception as exc:
        logger.error("Extraction failed for {}: {}", archive_path, exc)
        raise CorruptArchiveError(str(exc)) from exc


def _is_rar_ext(name: str) -> bool:
    import re
    return bool(re.search(r"\.(r\d{2}|part\d+\.rar)$", name, re.IGNORECASE))


# ─── Format-specific extractors ───────────────────────────────────────────────

def _extract_zip(path: str, dest: str, password: str | None) -> None:
    pwd = password.encode() if password else None
    try:
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(dest, pwd=pwd)
    except RuntimeError as exc:
        if "password" in str(exc).lower() or "Bad password" in str(exc):
            raise WrongPasswordError(str(exc)) from exc
        raise CorruptArchiveError(str(exc)) from exc
    except zipfile.BadZipFile as exc:
        raise CorruptArchiveError(str(exc)) from exc


def _extract_rar(path: str, dest: str, password: str | None) -> None:
    try:
        with rarfile.RarFile(path) as rf:
            if rf.needs_password() and not password:
                raise WrongPasswordError("Password required")
            rf.extractall(dest, pwd=password)
    except rarfile.BadRarFile as exc:
        raise CorruptArchiveError(str(exc)) from exc
    except rarfile.PasswordRequired as exc:
        raise WrongPasswordError(str(exc)) from exc
    except rarfile.BadRarName as exc:
        raise CorruptArchiveError(str(exc)) from exc


def _extract_7z(path: str, dest: str, password: str | None) -> None:
    try:
        with py7zr.SevenZipFile(path, mode="r", password=password) as zf:
            zf.extractall(path=dest)
    except py7zr.exceptions.PasswordRequired as exc:
        raise WrongPasswordError(str(exc)) from exc
    except py7zr.exceptions.Bad7zFile as exc:
        raise CorruptArchiveError(str(exc)) from exc


def _extract_tar(path: str, dest: str) -> None:
    import tarfile
    try:
        with tarfile.open(path, "r:*") as tf:
            # Security: prevent path traversal
            def safe_members(tf: tarfile.TarFile):
                for m in tf.getmembers():
                    if m.name.startswith("/") or ".." in m.name:
                        continue
                    yield m
            tf.extractall(dest, members=safe_members(tf))
    except tarfile.TarError as exc:
        raise CorruptArchiveError(str(exc)) from exc


def _extract_patool(path: str, dest: str, password: str | None) -> None:
    """Last-resort: use patool for exotic formats."""
    try:
        import patoollib
        kwargs: dict = {}
        if password:
            kwargs["password"] = password
        patoollib.extract_archive(path, outdir=dest, **kwargs)
    except Exception as exc:
        raise CorruptArchiveError(str(exc)) from exc
