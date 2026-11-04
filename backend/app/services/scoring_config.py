"""Scoring configuration block for boosts, penalties, and feedback weights."""

class ScoringConfig:
    # Step 2: Query intent boosts & penalties
    MOOD_BOOST: float = 0.15
    GENRE_BOOST: float = 0.10
    AVOID_PENALTY: float = 0.30

    # Step 4: Feedback reranker weights
    FEEDBACK_WEIGHT: float = 0.30
    FEEDBACK_DECAY_PER_DAY: float = 0.95
    SAVE_REPLAY_WEIGHT: float = 1.0
    SKIP_WEIGHT: float = 0.50

    # Step 3: Familiar mode tag affinity bonus
    FAMILIAR_AFFINITY_BONUS: float = 0.05

    # Candidate retrieval pool size
    TOP_CANDIDATES: int = 200

    # Step 5: Diversity max consecutive tracks by the same artist
    MAX_CONSECUTIVE_ARTIST: int = 2
