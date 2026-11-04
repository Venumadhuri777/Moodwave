import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger("moodwave.catalog")

class CatalogStore:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_loaded: bool = False
        self.missing_files: List[str] = []
        self.tracks: Dict[str, dict] = {}
        self.trending: List[dict] = []
        self.embeddings: Optional[np.ndarray] = None

    def load_data(self) -> Tuple[bool, List[str]]:
        self.missing_files = []
        self.tracks = {}
        self.trending = []
        self.embeddings = None

        catalog_path = self.data_dir / "catalog.csv"
        semantic_path = self.data_dir / "semantic_ids.csv"
        embeddings_path = self.data_dir / "embeddings.npy"
        trending_path = self.data_dir / "trending.json"

        # Check required files
        for name, path in [
            ("catalog.csv", catalog_path),
            ("semantic_ids.csv", semantic_path),
            ("embeddings.npy", embeddings_path),
        ]:
            if not path.is_file():
                self.missing_files.append(name)

        if self.missing_files:
            self.data_loaded = False
            logger.warning(
                "Catalog data files missing in %s: %s", self.data_dir, ", ".join(self.missing_files)
            )
            return False, self.missing_files

        try:
            # Load embeddings
            self.embeddings = np.load(embeddings_path)
            logger.info("Loaded embeddings of shape %s", self.embeddings.shape)

            # Load semantic IDs
            semantic_map: Dict[str, str] = {}
            with open(semantic_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    track_id = row.get("track_id", "").strip()
                    sem_id = row.get("semantic_id", "").strip()
                    if track_id:
                        semantic_map[track_id] = sem_id

            # Load catalog
            with open(catalog_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    track_id = row.get("track_id", "").strip()
                    if not track_id:
                        continue
                    genre_raw = row.get("genres", "") or row.get("primary_genre", "")
                    genres_list = [g.strip() for g in genre_raw.split("|") if g.strip()]
                    primary_genre = row.get("primary_genre", "") or (genres_list[0] if genres_list else "unknown")
                    mood_raw = row.get("mood_tags", "")
                    mood_list = [m.strip() for m in mood_raw.split("|") if m.strip()]

                    sem_id = semantic_map.get(track_id, "00-00-00")

                    self.tracks[track_id] = {
                        "track_id": track_id,
                        "title": row.get("title", track_id),
                        "artist": row.get("artist", "Unknown Artist"),
                        "album": row.get("album", None),
                        "genre": primary_genre,
                        "genres": genres_list,
                        "mood_tags": mood_list,
                        "semantic_id": sem_id,
                        "track_url": row.get("track_url", ""),
                        "duration_seconds": int(row["duration_seconds"]) if "duration_seconds" in row and row["duration_seconds"].isdigit() else None,
                        "license": row.get("license", "CC BY-NC-SA 4.0"),
                    }

            logger.info("Loaded %d catalog tracks from %s", len(self.tracks), catalog_path)

            # Load or fallback trending
            if trending_path.is_file():
                with open(trending_path, "r", encoding="utf-8") as f:
                    self.trending = json.load(f)
                logger.info("Loaded %d trending tracks from %s", len(self.trending), trending_path)
            else:
                self.trending = list(self.tracks.values())[:50]
                logger.info("Generated %d fallback trending tracks from catalog", len(self.trending))

            self.data_loaded = True
            return True, []
        except Exception as e:
            logger.error("Error loading catalog data: %s", e)
            self.data_loaded = False
            self.missing_files.append(f"Load error: {e}")
            return False, self.missing_files

    def get_track(self, track_id: str) -> Optional[dict]:
        return self.tracks.get(track_id)

    def get_recommendations(self, query: str, limit: int = 10) -> List[dict]:
        # TODO Part 5: real recommender
        # TODO Part 4: real intent parser
        # Placeholder ranking: filter trending tracks by simple keyword match against genre and mood tags
        query_words = set(query.lower().split())
        matched: List[dict] = []
        unmatched: List[dict] = []

        pool = self.trending if self.trending else list(self.tracks.values())

        for item in pool:
            # normalize item keys
            genre = item.get("genre", "")
            mood_tags = item.get("mood_tags", [])
            tag_words = set(genre.lower().split() + [t.lower() for t in mood_tags])

            if query_words.intersection(tag_words):
                matched.append(item)
            else:
                unmatched.append(item)

        results = matched + unmatched
        selected = results[:limit]

        formatted_items = []
        for track in selected:
            track_id = track.get("track_id", "")
            genre = track.get("genre", "music")
            mood_tags = track.get("mood_tags", [])
            formatted_items.append({
                "track_id": track_id,
                "title": track.get("title", track_id),
                "artist": track.get("artist", "Unknown Artist"),
                "genre": genre,
                "mood_tags": mood_tags,
                "explanation": f"Matched via placeholder ranking on query keywords for {genre}.",
                "semantic_id": track.get("semantic_id", "00-00-00"),
                "track_url": track.get("track_url", f"https://jamendo.com/track/{track_id}"),
            })

        return formatted_items
