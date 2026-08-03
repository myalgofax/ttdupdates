from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from loguru import logger

from models.events import Event, NewsItem, NotificationRecord, ScreenshotRecord, SessionRecord


class DatabaseService:
    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    screenshot_path TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL UNIQUE,
                    url TEXT,
                    content TEXT,
                    source TEXT DEFAULT 'TTD',
                    detected_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT NOT NULL,
                    auth_path TEXT,
                    created_at TEXT NOT NULL,
                    expires_at TEXT
                );
                CREATE TABLE IF NOT EXISTS screenshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    message TEXT NOT NULL,
                    sent INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );
            """)
        logger.info("Database initialized")

    # --- Events ---
    def save_event(self, event: Event) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO events (event_type, message, screenshot_path, created_at) VALUES (?,?,?,?)",
                (event.event_type.value, event.message, event.screenshot_path, event.created_at.isoformat()),
            )
            return cur.lastrowid  # type: ignore[return-value]

    # --- News ---
    def save_news(self, item: NewsItem) -> bool:
        """Returns True if new, False if duplicate."""
        try:
            with self._conn() as conn:
                conn.execute(
                    "INSERT INTO news (title, url, content, source, detected_at) VALUES (?,?,?,?,?)",
                    (item.title, item.url, item.content, item.source, item.detected_at.isoformat()),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def get_all_news_titles(self) -> set[str]:
        with self._conn() as conn:
            rows = conn.execute("SELECT title FROM news").fetchall()
        return {r["title"] for r in rows}

    # --- Sessions ---
    def save_session(self, session: SessionRecord) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO sessions (status, auth_path, created_at, expires_at) VALUES (?,?,?,?)",
                (session.status, session.auth_path, session.created_at.isoformat(),
                 session.expires_at.isoformat() if session.expires_at else None),
            )

    # --- Screenshots ---
    def save_screenshot(self, record: ScreenshotRecord) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO screenshots (context, file_path, created_at) VALUES (?,?,?)",
                (record.context, record.file_path, record.created_at.isoformat()),
            )

    def get_old_screenshots(self, older_than_days: int) -> list[str]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT file_path FROM screenshots WHERE created_at < datetime('now', ?)",
                (f"-{older_than_days} days",),
            ).fetchall()
        return [r["file_path"] for r in rows]

    def delete_old_screenshots(self, older_than_days: int) -> None:
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM screenshots WHERE created_at < datetime('now', ?)",
                (f"-{older_than_days} days",),
            )

    # --- Notifications ---
    def save_notification(self, record: NotificationRecord) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO notifications (channel, message, sent, created_at) VALUES (?,?,?,?)",
                (record.channel, record.message, int(record.sent), record.created_at.isoformat()),
            )
