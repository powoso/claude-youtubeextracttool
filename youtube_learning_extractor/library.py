"""Personal library — SQLite persistence with full-text search."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from .models import VideoAnalysis

DEFAULT_DB_PATH = os.path.join(Path.home(), ".yt_learn_library.db")


class Library:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                summary TEXT NOT NULL,
                key_takeaways TEXT NOT NULL,
                actionable_insights TEXT NOT NULL,
                flashcards TEXT NOT NULL,
                transcript_length INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS videos_fts USING fts5(
                video_id,
                title,
                summary,
                key_takeaways,
                actionable_insights,
                content=videos,
                content_rowid=rowid
            );

            CREATE TRIGGER IF NOT EXISTS videos_ai AFTER INSERT ON videos BEGIN
                INSERT INTO videos_fts(rowid, video_id, title, summary, key_takeaways, actionable_insights)
                VALUES (new.rowid, new.video_id, new.title, new.summary, new.key_takeaways, new.actionable_insights);
            END;

            CREATE TRIGGER IF NOT EXISTS videos_ad AFTER DELETE ON videos BEGIN
                INSERT INTO videos_fts(videos_fts, rowid, video_id, title, summary, key_takeaways, actionable_insights)
                VALUES ('delete', old.rowid, old.video_id, old.title, old.summary, old.key_takeaways, old.actionable_insights);
            END;
            """
        )
        self._conn.commit()

    def save(self, analysis: VideoAnalysis) -> None:
        """Save or replace a video analysis in the library."""
        d = analysis.to_dict()
        self._conn.execute(
            """
            INSERT OR REPLACE INTO videos
                (video_id, title, url, summary, key_takeaways,
                 actionable_insights, flashcards, transcript_length, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                d["video_id"],
                d["title"],
                d["url"],
                d["summary"],
                json.dumps(d["key_takeaways"]),
                json.dumps(d["actionable_insights"]),
                json.dumps(d["flashcards"]),
                d["transcript_length"],
                d["created_at"],
            ),
        )
        self._conn.commit()

    def get(self, video_id: str) -> VideoAnalysis | None:
        """Retrieve a single analysis by video ID."""
        row = self._conn.execute(
            "SELECT * FROM videos WHERE video_id = ?", (video_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_analysis(row)

    def list_all(self) -> list[VideoAnalysis]:
        """List all saved analyses, most recent first."""
        rows = self._conn.execute(
            "SELECT * FROM videos ORDER BY created_at DESC"
        ).fetchall()
        return [self._row_to_analysis(r) for r in rows]

    def search(self, query: str) -> list[VideoAnalysis]:
        """Full-text search across titles, summaries, takeaways, and insights."""
        rows = self._conn.execute(
            """
            SELECT v.* FROM videos v
            JOIN videos_fts fts ON v.rowid = fts.rowid
            WHERE videos_fts MATCH ?
            ORDER BY rank
            """,
            (query,),
        ).fetchall()
        return [self._row_to_analysis(r) for r in rows]

    def delete(self, video_id: str) -> bool:
        """Delete a video analysis. Returns True if it existed."""
        cur = self._conn.execute(
            "DELETE FROM videos WHERE video_id = ?", (video_id,)
        )
        self._conn.commit()
        return cur.rowcount > 0

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def _row_to_analysis(row: sqlite3.Row) -> VideoAnalysis:
        data = dict(row)
        data["key_takeaways"] = json.loads(data["key_takeaways"])
        data["actionable_insights"] = json.loads(data["actionable_insights"])
        data["flashcards"] = json.loads(data["flashcards"])
        return VideoAnalysis.from_dict(data)
