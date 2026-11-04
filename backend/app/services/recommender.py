import logging
from typing import List, Optional, Set, Tuple
import numpy as np
from app.services.feedback_model import FeedbackModel
from app.services.index import CatalogIndex
from app.services.intent_schema import Intent
from app.services.query_vector import compute_query_score, encode_query
from app.services.scoring_config import ScoringConfig

logger = logging.getLogger("moodwave.recommender")

class Recommender:
    def __init__(self, index: CatalogIndex, feedback_model: Optional[FeedbackModel] = None):
        self.index = index
        self.feedback_model = feedback_model

    def recommend(
        self,
        query: str,
        user_id: str,
        mode: str = "familiar",
        intent: Optional[Intent] = None,
        limit: int = 10,
    ) -> Tuple[List[dict], bool, Optional[str]]:
        """Executes the full Moodwave recommendation pipeline:
        1. Encodes query or flags embedding_unavailable.
        2. Retrieves top candidates.
        3. Filters out 24h skips.
        4. Applies mode-specific filtering/scoring (familiar vs. non-habitual).
        5. Incorporates user feedback preference vector.
        6. Applies artist diversity pass.
        7. Synthesizes 1-line transparent rationales.
        Returns: (items, degraded, degraded_reason)
        """
        if not self.index.is_loaded or len(self.index.tracks) == 0:
            return [], True, "catalog_not_loaded"

        degraded = False
        degraded_reasons = []

        # 1. Encode query vector
        query_vec = encode_query(query)
        if query_vec is None:
            degraded = True
            degraded_reasons.append("embedding_unavailable")

        # 2. Filter out tracks skipped in last 24h
        skipped_24h: Set[str] = set()
        user_history_track_ids: List[str] = []
        user_vector: Optional[np.ndarray] = None

        if self.feedback_model is not None:
            skipped_24h = self.feedback_model.get_skipped_tracks_last_24h(user_id)
            user_history_track_ids = self.feedback_model.get_user_saved_or_replayed_tracks(user_id, limit=50)
            user_vector = self.feedback_model.get_user_vector(user_id)

        # 3. Retrieve candidates
        # Vector search top 200 candidates
        candidate_indices = [
            idx for idx, t in enumerate(self.index.tracks)
            if t["track_id"] not in skipped_24h
        ]
        if not candidate_indices:
            # Fallback to all tracks if everything was skipped
            candidate_indices = list(range(len(self.index.tracks)))

        # Retrieve top 200 candidates by vector search (or first 200 if query_vec is None)
        raw_candidates = self.index.vector_search(
            query_vec=query_vec,
            top_k=ScoringConfig.TOP_CANDIDATES,
            candidate_indices=candidate_indices,
        )

        # 4. Mode-specific handling & Affinity Bonus
        # History level-1 codes and prefixes for non-habitual exclusion
        history_level1_codes: Set[str] = set()
        history_prefixes: Set[str] = set()
        user_affinity_tags: Set[str] = set()

        for t_id in user_history_track_ids:
            hist_track = self.index.get_track_by_id(t_id)
            if hist_track:
                history_level1_codes.add(hist_track["code1"])
                history_prefixes.add(hist_track["prefix"])
                user_affinity_tags.add(hist_track["genre"])
                user_affinity_tags.update(hist_track.get("mood_tags", []))

        # Score each candidate
        scored_candidates: List[dict] = []
        for idx, base_sim in raw_candidates:
            track = self.index.get_track_by_index(idx)
            if not track:
                continue

            track_emb = self.index.get_embedding(track["track_id"])
            q_score, breakdown = compute_query_score(
                track=track,
                track_embedding=track_emb,
                query_embedding=query_vec,
                intent=intent,
            )

            # Step 4: User vector feedback term
            feedback_term = 0.0
            if user_vector is not None and track_emb is not None:
                feedback_term = ScoringConfig.FEEDBACK_WEIGHT * float(np.dot(track_emb, user_vector))

            # Step 3: Familiar mode affinity bonus
            affinity_bonus = 0.0
            if mode == "familiar":
                # Check overlap with user's saved/replayed genre and mood tags
                track_tags = set([track["genre"]] + track.get("mood_tags", []))
                overlap = len(track_tags.intersection(user_affinity_tags))
                affinity_bonus = ScoringConfig.FAMILIAR_AFFINITY_BONUS * overlap

            final_score = q_score + feedback_term + affinity_bonus

            scored_candidates.append({
                "track": track,
                "score": final_score,
                "breakdown": breakdown,
                "track_id": track["track_id"],
                "code1": track["code1"],
                "prefix": track["prefix"],
                "artist": track["artist"],
            })

        # Sort candidates by final_score descending (stable sort with track_id tie-breaker)
        scored_candidates.sort(key=lambda x: (-x["score"], x["track_id"]))

        # Apply non-habitual filtering if mode == "non_habitual"
        final_pool = scored_candidates
        if mode == "non_habitual" and history_level1_codes:
            # Level 1 exclusion: remove tracks whose code1 is in user's last 50 tracks
            filtered = [c for c in scored_candidates if c["code1"] not in history_level1_codes]

            if len(filtered) < 10:
                # Relax to level-2 prefix exclusion
                filtered = [c for c in scored_candidates if c["prefix"] not in history_prefixes]
                degraded = True
                degraded_reasons.append("non_habitual_relaxed")

                if len(filtered) < 10:
                    # Relax completely
                    filtered = scored_candidates
                    degraded = True
                    if "non_habitual_relaxed" not in degraded_reasons:
                        degraded_reasons.append("non_habitual_relaxed")

            final_pool = filtered

        # Step 5: Diversity pass (no more than 2 consecutive tracks by the same artist)
        diversified_pool = self._apply_artist_diversity(
            final_pool, max_consecutive=ScoringConfig.MAX_CONSECUTIVE_ARTIST
        )

        # Slice to requested limit
        selected = diversified_pool[:limit]

        # Step 6: Generate one-line rationales
        items = []
        for cand in selected:
            track = cand["track"]
            breakdown = cand["breakdown"]
            explanation = self._build_explanation(track, mode, breakdown, intent)

            items.append({
                "track_id": track["track_id"],
                "title": track["title"],
                "artist": track["artist"],
                "genre": track["genre"],
                "mood_tags": track["mood_tags"],
                "explanation": explanation,
                "semantic_id": track["semantic_id"],
                "track_url": track["track_url"],
            })

        combined_reason = ", ".join(degraded_reasons) if degraded_reasons else None
        return items, degraded, combined_reason

    def _apply_artist_diversity(self, pool: List[dict], max_consecutive: int = 2) -> List[dict]:
        """Ensures no more than max_consecutive tracks share the same artist using stable order."""
        result: List[dict] = []
        remaining = list(pool)

        while remaining:
            chosen_idx = None
            for i, cand in enumerate(remaining):
                artist = cand.get("artist")
                if len(result) >= max_consecutive:
                    prev_artists = [r.get("artist") for r in result[-max_consecutive:]]
                    if all(a == artist for a in prev_artists):
                        continue
                chosen_idx = i
                break

            if chosen_idx is None:
                chosen_idx = 0

            result.append(remaining.pop(chosen_idx))

        return result

    def _build_explanation(
        self,
        track: dict,
        mode: str,
        breakdown: dict,
        intent: Optional[Intent],
    ) -> str:
        matched_moods = breakdown.get("matched_moods", [])
        matched_genres = breakdown.get("matched_genres", [])
        genre = track.get("genre", "music")

        if mode == "non_habitual":
            if matched_moods:
                return f"Fresh discovery in {genre} matching your '{matched_moods[0]}' vibe outside your habitual cluster."
            return f"Explores novel {genre} sonic territory outside your habitual listening history."

        # Familiar mode
        if matched_moods and matched_genres:
            return f"Selected for {matched_moods[0]} focus with comforting {genre} textures."
        elif matched_moods:
            return f"Matches your {matched_moods[0]} mood with signature {genre} elements."
        elif matched_genres:
            return f"Fits your {genre} genre preference with smooth flow."
        elif intent and intent.context:
            return f"Curated to accompany your {intent.context} with {genre} soundscapes."
        else:
            return f"Recommended to fit your listening moment in {genre}."
