import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger("moodwave.index")

class CatalogIndex:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.tracks: List[dict] = []
        self.track_id_to_index: Dict[str, int] = {}
        self.index_to_track_id: Dict[int, str] = {}
        self.embeddings: Optional[np.ndarray] = None
        self.codebooks: Optional[Dict[str, np.ndarray]] = None

        # Prefix maps: level1 -> list of row indices, (level1-level2) -> list of row indices
        self.level1_map: Dict[str, List[int]] = {}
        self.prefix_map: Dict[str, List[int]] = {}
        self.is_loaded: bool = False

    def load(self) -> bool:
        catalog_path = self.data_dir / "catalog.csv"
        semantic_path = self.data_dir / "semantic_ids.csv"
        embeddings_path = self.data_dir / "embeddings.npy"
        codebooks_path = self.data_dir / "codebooks.npz"

        for p in [catalog_path, semantic_path, embeddings_path]:
            if not p.is_file():
                logger.error("CatalogIndex missing required file: %s", p)
                self.is_loaded = False
                return False

        try:
            # 1. Load embeddings
            self.embeddings = np.load(embeddings_path).astype(np.float32)
            # Ensure L2 normalization
            norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.embeddings = self.embeddings / norms
            logger.info("Loaded embeddings of shape %s", self.embeddings.shape)

            # 2. Load semantic IDs
            semantic_data: Dict[str, dict] = {}
            with open(semantic_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    t_id = row.get("track_id", "").strip()
                    if t_id:
                        c1 = f"{int(row.get('code1', 0)):02d}"
                        c2 = f"{int(row.get('code2', 0)):02d}"
                        c3 = f"{int(row.get('code3', 0)):02d}"
                        sem_id = row.get("semantic_id", f"{c1}-{c2}-{c3}")
                        semantic_data[t_id] = {
                            "code1": c1,
                            "code2": c2,
                            "code3": c3,
                            "prefix": f"{c1}-{c2}",
                            "semantic_id": sem_id,
                        }

            # 3. Load catalog
            self.tracks = []
            self.track_id_to_index = {}
            self.index_to_track_id = {}
            self.level1_map = {}
            self.prefix_map = {}

            with open(catalog_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    t_id = row.get("track_id", "").strip()
                    if not t_id:
                        continue

                    sem_info = semantic_data.get(t_id, {
                        "code1": "00",
                        "code2": "00",
                        "code3": "00",
                        "prefix": "00-00",
                        "semantic_id": "00-00-00",
                    })

                    raw_genres = row.get("genres", "") or row.get("primary_genre", "")
                    genres_list = [g.strip().lower() for g in raw_genres.split("|") if g.strip()]
                    primary_genre = row.get("primary_genre", "") or (genres_list[0] if genres_list else "unknown")
                    raw_moods = row.get("mood_tags", "")
                    mood_list = [m.strip().lower() for m in raw_moods.split("|") if m.strip()]

                    track_obj = {
                        "index": idx,
                        "track_id": t_id,
                        "title": row.get("title", t_id),
                        "artist": row.get("artist", "Unknown Artist"),
                        "album": row.get("album", None),
                        "genre": primary_genre,
                        "genres": genres_list,
                        "mood_tags": mood_list,
                        "code1": sem_info["code1"],
                        "code2": sem_info["code2"],
                        "code3": sem_info["code3"],
                        "prefix": sem_info["prefix"],
                        "semantic_id": sem_info["semantic_id"],
                        "track_url": row.get("track_url", f"https://jamendo.com/track/{t_id}"),
                    }

                    self.tracks.append(track_obj)
                    self.track_id_to_index[t_id] = idx
                    self.index_to_track_id[idx] = t_id

                    # Populate prefix maps
                    c1 = sem_info["code1"]
                    prefix = sem_info["prefix"]
                    self.level1_map.setdefault(c1, []).append(idx)
                    self.prefix_map.setdefault(prefix, []).append(idx)

            # 4. Load codebooks if present
            if codebooks_path.is_file():
                try:
                    cb = np.load(codebooks_path)
                    self.codebooks = {k: cb[k] for k in cb.files}
                    logger.info("Loaded codebooks from %s with keys: %s", codebooks_path, list(self.codebooks.keys()))
                except Exception as e:
                    logger.warning("Failed to load codebooks: %s", e)
                    self.codebooks = None

            self.is_loaded = True
            logger.info("CatalogIndex successfully loaded with %d tracks", len(self.tracks))
            return True
        except Exception as e:
            logger.error("Failed to load CatalogIndex: %s", e, exc_info=True)
            self.is_loaded = False
            return False

    def vector_search(
        self,
        query_vec: Optional[np.ndarray],
        top_k: int = 200,
        candidate_indices: Optional[List[int]] = None,
    ) -> List[Tuple[int, float]]:
        if not self.is_loaded or self.embeddings is None:
            return []

        if candidate_indices is None:
            candidate_indices = list(range(len(self.tracks)))

        if not candidate_indices:
            return []

        if query_vec is not None:
            # Normalize query vector if needed
            q_norm = np.linalg.norm(query_vec)
            if q_norm > 0:
                q_vec = query_vec / q_norm
            else:
                q_vec = query_vec

            cand_embs = self.embeddings[candidate_indices]
            sims = np.dot(cand_embs, q_vec)

            # Retrieve top candidates
            k = min(top_k, len(candidate_indices))
            sorted_local_indices = np.argsort(-sims)[:k]
            return [(candidate_indices[i], float(sims[i])) for i in sorted_local_indices]
        else:
            k = min(top_k, len(candidate_indices))
            return [(idx, 0.0) for idx in candidate_indices[:k]]

    def get_track_by_index(self, idx: int) -> Optional[dict]:
        if 0 <= idx < len(self.tracks):
            return self.tracks[idx]
        return None

    def get_track_by_id(self, track_id: str) -> Optional[dict]:
        idx = self.track_id_to_index.get(track_id)
        if idx is not None:
            return self.tracks[idx]
        return None

    def get_embedding(self, track_id: str) -> Optional[np.ndarray]:
        idx = self.track_id_to_index.get(track_id)
        if idx is not None and self.embeddings is not None:
            return self.embeddings[idx]
        return None
