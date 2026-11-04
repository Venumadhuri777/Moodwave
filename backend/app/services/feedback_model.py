import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Set
import numpy as np
from app.services.scoring_config import ScoringConfig

logger = logging.getLogger("moodwave.feedback_model")

class FeedbackModel:
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
                    CREATE TABLE IF NOT EXISTS user_vectors (
                        user_id TEXT PRIMARY KEY,
                        vector BLOB NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
            self.is_ok = True
            logger.info("user_vectors SQLite table initialized at %s", self.db_path)
            return True
        except Exception as e:
            logger.error("Failed to initialize user_vectors table: %s", e)
            self.is_ok = False
            return False

    def update_user_vector(self, user_id: str, track_embedding: np.ndarray, action: str):
        if not self.is_ok or track_embedding is None:
            return

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT vector, updated_at FROM user_vectors WHERE user_id = ?",
                    (user_id,),
                )
                row = cursor.fetchone()

                if row is not None:
                    raw_blob, last_iso = row
                    current_vec = np.frombuffer(raw_blob, dtype=np.float32).copy()
                    try:
                        last_time = datetime.fromisoformat(last_iso)
                        days = (now - last_time).total_seconds() / 86400.0
                        decay = ScoringConfig.FEEDBACK_DECAY_PER_DAY ** max(0.0, days)
                        current_vec = current_vec * decay
                    except Exception:
                        pass
                else:
                    current_vec = np.zeros_like(track_embedding, dtype=np.float32)

                # Apply action weight
                if action in ("save", "replay"):
                    current_vec += ScoringConfig.SAVE_REPLAY_WEIGHT * track_embedding
                elif action == "skip":
                    current_vec -= ScoringConfig.SKIP_WEIGHT * track_embedding

                blob = current_vec.tobytes()
                cursor.execute(
                    """
                    INSERT INTO user_vectors (user_id, vector, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        vector = excluded.vector,
                        updated_at = excluded.updated_at
                    """,
                    (user_id, blob, now_iso),
                )
                conn.commit()
        except Exception as e:
            logger.error("Failed to update user vector for %s: %s", user_id, e)

    def get_user_vector(self, user_id: str) -> Optional[np.ndarray]:
        if not self.is_ok:
            return None

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT vector, updated_at FROM user_vectors WHERE user_id = ?",
                    (user_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None

                raw_blob, last_iso = row
                vec = np.frombuffer(raw_blob, dtype=np.float32).copy()
                now = datetime.now(timezone.utc)
                try:
                    last_time = datetime.fromisoformat(last_iso)
                    days = (now - last_time).total_seconds() / 86400.0
                    decay = ScoringConfig.FEEDBACK_DECAY_PER_DAY ** max(0.0, days)
                    vec = vec * decay
                except Exception:
                    pass

                norm = np.linalg.norm(vec)
                if norm > 0:
                    return vec / norm
                return None
        except Exception as e:
            logger.error("Error retrieving user vector for %s: %s", user_id, e)
            return None

    def get_skipped_tracks_last_24h(self, user_id: str) -> Set[str]:
        if not self.is_ok:
            return set()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 24 hours ago
                cursor.execute(
                    """
                    SELECT track_id FROM feedback
                    WHERE user_id = ? AND action = 'skip'
                    AND datetime(created_at) >= datetime('now', '-1 day')
                    """,
                    (user_id,),
                )
                return {row[0] for row in cursor.fetchall()}
        except Exception as e:
            logger.error("Error querying 24h skipped tracks for %s: %s", user_id, e)
            return set()

    def get_user_saved_or_replayed_tracks(self, user_id: str, limit: int = 50) -> List[str]:
        if not self.is_ok:
            return []

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT track_id FROM feedback
                    WHERE user_id = ? AND action IN ('save', 'replay')
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (user_id, limit),
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Error querying saved/replayed tracks for %s: %s", user_id, e)
            return []
