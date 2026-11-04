import logging
from typing import Optional, Tuple
import numpy as np
from app.services.intent_schema import Intent
from app.services.scoring_config import ScoringConfig

logger = logging.getLogger("moodwave.query_vector")

# Global lazy model cache
_MODEL = None
_MODEL_FAILED = False

def get_sentence_transformer():
    global _MODEL, _MODEL_FAILED
    if _MODEL is not None:
        return _MODEL
    if _MODEL_FAILED:
        return None

    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading SentenceTransformer('all-MiniLM-L6-v2')...")
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        return _MODEL
    except Exception as e:
        logger.warning(
            "SentenceTransformer not available or failed to load: %s. Using boost-only fallback.", e
        )
        _MODEL_FAILED = True
        return None

def encode_query(query: str) -> Optional[np.ndarray]:
    if not query or not query.strip():
        return None

    model = get_sentence_transformer()
    if model is None:
        return None

    try:
        vec = model.encode(query.strip(), convert_to_numpy=True).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            return vec / norm
        return vec
    except Exception as e:
        logger.warning("Query vector encoding failed: %s", e)
        return None

def compute_query_score(
    track: dict,
    track_embedding: Optional[np.ndarray],
    query_embedding: Optional[np.ndarray],
    intent: Optional[Intent],
) -> Tuple[float, dict]:
    """Computes: query_score = cosine(query_vec, track_vec) + boosts - penalties.
    Returns: (query_score, score_breakdown)
    """
    # 1. Base cosine vector similarity
    if track_embedding is not None and query_embedding is not None:
        vector_sim = float(np.dot(track_embedding, query_embedding))
    else:
        vector_sim = 0.0

    # 2. Tag boosts and penalties
    mood_boost = 0.0
    genre_boost = 0.0
    avoid_penalty = 0.0
    matched_moods = []
    matched_genres = []

    if intent is not None:
        track_moods = set(track.get("mood_tags", []))
        track_genres = set(track.get("genres", []) + [track.get("genre", "")])

        for m in intent.moods:
            if m in track_moods:
                mood_boost += ScoringConfig.MOOD_BOOST
                matched_moods.append(m)

        for g in intent.genres:
            if g in track_genres:
                genre_boost += ScoringConfig.GENRE_BOOST
                matched_genres.append(g)

        for ag in intent.avoid_genres:
            if ag in track_genres:
                avoid_penalty += ScoringConfig.AVOID_PENALTY

    query_score = vector_sim + mood_boost + genre_boost - avoid_penalty

    breakdown = {
        "vector_sim": vector_sim,
        "mood_boost": mood_boost,
        "genre_boost": genre_boost,
        "avoid_penalty": avoid_penalty,
        "matched_moods": matched_moods,
        "matched_genres": matched_genres,
    }

    return query_score, breakdown
