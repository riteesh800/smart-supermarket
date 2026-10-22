"""
Persistent upload state storage — SQLite-backed.
Replaces in-memory _pending_uploads / _feature_flags / _mapping_info dicts
so they survive process restarts and work with multiple workers.
Strictly isolates feature flags, mappings, and pending uploads per user.
"""

import sqlite3
import json
import uuid
import time
import os
import threading
from typing import Optional

_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload_state.db")
_lock = threading.Lock()
_TTL_SECONDS = 3600  # 1 hour


def _get_conn():
    conn = sqlite3.connect(_DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _ensure_tables():
    with _lock:
        conn = _get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_uploads (
                id TEXT PRIMARY KEY,
                content BLOB NOT NULL,
                created_at REAL NOT NULL,
                user_id TEXT DEFAULT ''
            )
        """)
        # Ensure user_id column exists if table was created previously
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(pending_uploads)").fetchall()]
            if "user_id" not in cols:
                conn.execute("ALTER TABLE pending_uploads ADD COLUMN user_id TEXT DEFAULT ''")
        except Exception:
            pass

        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.commit()
        conn.close()


_ensure_tables()


def _cleanup_expired():
    """Remove uploads older than TTL."""
    cutoff = time.time() - _TTL_SECONDS
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM pending_uploads WHERE created_at < ?", (cutoff,))
        conn.commit()
    finally:
        conn.close()


def generate_upload_id():
    """Generate a unique upload ID using uuid4."""
    return str(uuid.uuid4())


def store_upload(upload_id: str, content: bytes, user_id: Optional[str] = None):
    """Store uploaded file content for later import."""
    _cleanup_expired()
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO pending_uploads (id, content, created_at, user_id) VALUES (?, ?, ?, ?)",
            (upload_id, content, time.time(), user_id or "")
        )
        conn.commit()
    finally:
        conn.close()


def get_upload(upload_id: str, user_id: Optional[str] = None) -> bytes | None:
    """Retrieve stored upload content. Returns None if expired, not found, or user mismatch."""
    _cleanup_expired()
    conn = _get_conn()
    try:
        if user_id:
            row = conn.execute(
                "SELECT content FROM pending_uploads WHERE id = ? AND (user_id = ? OR user_id = '' OR user_id IS NULL)",
                (upload_id, user_id)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT content FROM pending_uploads WHERE id = ?", (upload_id,)
            ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def remove_upload(upload_id: str):
    """Remove a consumed upload."""
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM pending_uploads WHERE id = ?", (upload_id,))
        conn.commit()
    finally:
        conn.close()


def clear_all_uploads(user_id: Optional[str] = None):
    """Clear pending uploads (optionally for a specific user)."""
    conn = _get_conn()
    try:
        if user_id:
            conn.execute("DELETE FROM pending_uploads WHERE user_id = ?", (user_id,))
        else:
            conn.execute("DELETE FROM pending_uploads")
        conn.commit()
    finally:
        conn.close()


# ── Feature Flags & Mapping Info (Strictly User-Scoped) ──

def get_state(key: str, default=None):
    """Get a JSON-serialized state value."""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT value FROM app_state WHERE key = ?", (key,)).fetchone()
        if row:
            return json.loads(row[0])
        return default
    finally:
        conn.close()


def set_state(key: str, value):
    """Set a JSON-serialized state value."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO app_state (key, value, updated_at) VALUES (?, ?, ?)",
            (key, json.dumps(value), time.time())
        )
        conn.commit()
    finally:
        conn.close()


def get_feature_flags(user_id: Optional[str] = None) -> dict:
    """Get feature flags for the current user. Returns unauthenticated/empty flags if no user_id."""
    if not user_id:
        return {"has_data": False}
    return get_state(f"feature_flags:{user_id}", default={})


def set_feature_flags(flags: dict, user_id: Optional[str] = None):
    """Persist feature flags for a specific user."""
    if user_id:
        set_state(f"feature_flags:{user_id}", flags)
    else:
        set_state("feature_flags", flags)


def get_mapping_info(user_id: Optional[str] = None) -> dict:
    """Get mapping info for a specific user."""
    if not user_id:
        return {}
    return get_state(f"mapping_info:{user_id}", default={})


def set_mapping_info(info: dict, user_id: Optional[str] = None):
    """Persist mapping info for a specific user."""
    if user_id:
        set_state(f"mapping_info:{user_id}", info)
    else:
        set_state("mapping_info", info)
