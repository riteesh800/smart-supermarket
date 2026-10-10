"""
Persistent upload state storage — SQLite-backed.
Replaces in-memory _pending_uploads / _feature_flags / _mapping_info dicts
so they survive process restarts and work with multiple workers.
Uses uuid4 for upload IDs and auto-cleans entries older than 1 hour.
"""

import sqlite3
import json
import uuid
import time
import os
import threading

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
                created_at REAL NOT NULL
            )
        """)
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


def store_upload(upload_id: str, content: bytes):
    """Store uploaded file content for later import."""
    _cleanup_expired()
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO pending_uploads (id, content, created_at) VALUES (?, ?, ?)",
            (upload_id, content, time.time())
        )
        conn.commit()
    finally:
        conn.close()


def get_upload(upload_id: str) -> bytes | None:
    """Retrieve stored upload content. Returns None if expired or not found."""
    _cleanup_expired()
    conn = _get_conn()
    try:
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


def clear_all_uploads():
    """Clear all pending uploads."""
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM pending_uploads")
        conn.commit()
    finally:
        conn.close()


# ── Feature Flags & Mapping Info ──

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


def get_feature_flags():
    """Get feature flags, with lazy initialization from DB data."""
    return get_state("feature_flags", default={})


def set_feature_flags(flags: dict):
    """Persist feature flags."""
    set_state("feature_flags", flags)


def get_mapping_info():
    """Get mapping info for all uploaded file types."""
    return get_state("mapping_info", default={})


def set_mapping_info(info: dict):
    """Persist mapping info."""
    set_state("mapping_info", info)
