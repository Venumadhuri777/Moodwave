import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("moodwave.feedback")

class FeedbackStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.is_ok = False

    def init_db(self) -> bool:
        try:
            path_obj = Path(self.db_path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        track_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
            self.is_ok = True
            logger.info("Feedback SQLite database initialized at %s", self.db_path)
            return True
        except Exception as e:
            self.is_ok = False
            logger.error("Failed to initialize feedback database at %s: %s", self.db_path, e)
            return False

    def record_feedback(self, user_id: str, track_id: str, action: str) -> dict:
        if not self.is_ok:
            raise RuntimeError("Feedback database is unavailable")
        
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO feedback (user_id, track_id, action, created_at) VALUES (?, ?, ?, ?)",
                    (user_id, track_id, action, now_iso),
                )
                conn.commit()
            return {
                "status": "recorded",
                "user_id": user_id,
                "track_id": track_id,
                "action": action,
                "timestamp": now_iso,
            }
        except Exception as e:
            logger.error("Failed to insert feedback row: %s", e)
            raise RuntimeError(f"Database error while recording feedback: {e}")
