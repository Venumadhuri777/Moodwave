import numpy as np
import pytest
from app.config import settings
from app.services.feedback_model import FeedbackModel
from app.services.index import CatalogIndex
from app.services.intent_schema import Intent
from app.services.query_vector import compute_query_score
from app.services.recommender import Recommender
from app.services.scoring_config import ScoringConfig

@pytest.fixture
def test_index():
    index = CatalogIndex(data_dir=settings.DATA_DIR)
    assert index.load() is True
    return index

@pytest.fixture
def test_feedback_model(tmp_path):
    db_path = str(tmp_path / "test_feedback.db")
    model = FeedbackModel(db_path=db_path)
    assert model.init_db() is True
    return model

def test_index_loading_and_prefix_maps(test_index):
    assert test_index.is_loaded is True
    assert len(test_index.tracks) > 0
    assert len(test_index.level1_map) > 0
    assert len(test_index.prefix_map) > 0

    # Ensure vector search returns results
    dummy_query = np.random.randn(384).astype(np.float32)
    dummy_query /= np.linalg.norm(dummy_query)
    results = test_index.vector_search(dummy_query, top_k=20)
    assert len(results) <= 20
    assert len(results) > 0

def test_query_vector_boosts_and_penalties(test_index):
    track = {
        "genre": "ambient",
        "genres": ["ambient", "drone"],
        "mood_tags": ["calm", "sleep"],
    }
    dummy_emb = np.random.randn(384).astype(np.float32)
    dummy_emb /= np.linalg.norm(dummy_emb)

    intent = Intent(
        moods=["calm"],
        genres=["ambient"],
        avoid_genres=["rock"],
    )

    score, breakdown = compute_query_score(
        track=track,
        track_embedding=dummy_emb,
        query_embedding=dummy_emb,
        intent=intent,
    )

    # Base cosine similarity is 1.0 (identical vector)
    # mood_boost: 0.15, genre_boost: 0.10, avoid_penalty: 0.0
    expected_score = 1.0 + ScoringConfig.MOOD_BOOST + ScoringConfig.GENRE_BOOST
    assert pytest.approx(score, 0.01) == expected_score
    assert breakdown["matched_moods"] == ["calm"]
    assert "ambient" in breakdown["matched_genres"]

    # Now test avoid_penalty
    penalty_intent = Intent(
        moods=[],
        genres=[],
        avoid_genres=["ambient"],
    )
    score2, breakdown2 = compute_query_score(
        track=track,
        track_embedding=dummy_emb,
        query_embedding=dummy_emb,
        intent=penalty_intent,
    )
    assert pytest.approx(score2, 0.01) == 1.0 - ScoringConfig.AVOID_PENALTY

def test_feedback_model_user_vector_and_decay(test_feedback_model):
    user_id = "user-test-feedback-999"
    emb1 = np.ones(384, dtype=np.float32)

    # 1. Save track (+1.0)
    test_feedback_model.update_user_vector(user_id, emb1, action="save")
    vec = test_feedback_model.get_user_vector(user_id)
    assert vec is not None
    assert pytest.approx(np.linalg.norm(vec), 0.01) == 1.0

    # 2. Skip track (-0.5)
    test_feedback_model.update_user_vector(user_id, emb1, action="skip")
    vec2 = test_feedback_model.get_user_vector(user_id)
    assert vec2 is not None

def test_recommender_familiar_and_non_habitual_modes(test_index, test_feedback_model):
    recommender = Recommender(index=test_index, feedback_model=test_feedback_model)
    user_id = "user-test-modes-1234"
    query = "calm ambient study"
    intent = Intent(moods=["calm", "study"], genres=["ambient", "lofi"])

    # 1. Familiar mode
    items_fam, degraded_fam, reason_fam = recommender.recommend(
        query=query, user_id=user_id, mode="familiar", intent=intent, limit=10
    )
    assert len(items_fam) == 10
    for item in items_fam:
        assert "track_id" in item
        assert "explanation" in item
        assert len(item["explanation"]) > 0

    # 2. Non-habitual mode with user history
    # Record some tracks as saved by the user
    saved_tracks = [t["track_id"] for t in items_fam[:5]]
    for t_id in saved_tracks:
        test_index_track = test_index.get_track_by_id(t_id)
        if test_index_track:
            emb = test_index.get_embedding(t_id)
            test_feedback_model.update_user_vector(user_id, emb, action="save")

    items_nonhab, degraded_nonhab, reason_nonhab = recommender.recommend(
        query=query, user_id=user_id, mode="non_habitual", intent=intent, limit=10
    )
    assert len(items_nonhab) == 10
    for item in items_nonhab:
        assert "Fresh discovery" in item["explanation"] or "sonic territory" in item["explanation"]

def test_artist_diversity_constraint(test_index, test_feedback_model):
    recommender = Recommender(index=test_index, feedback_model=test_feedback_model)

    # Create artificial pool with same artist repeated 5 times
    pool = [
        {"track_id": "t1", "artist": "SameArtist", "score": 10},
        {"track_id": "t2", "artist": "SameArtist", "score": 9},
        {"track_id": "t3", "artist": "SameArtist", "score": 8},
        {"track_id": "t4", "artist": "OtherArtist1", "score": 7},
        {"track_id": "t5", "artist": "OtherArtist2", "score": 6},
    ]

    diversified = recommender._apply_artist_diversity(pool, max_consecutive=2)
    # Check that no 3 consecutive elements have SameArtist
    artists = [cand["artist"] for cand in diversified]
    for i in range(len(artists) - 2):
        assert not (artists[i] == artists[i+1] == artists[i+2])

def test_skipped_tracks_filtered_out(test_index, tmp_path):
    # Use real SQLite feedback DB to test 24h skip filtering
    import sqlite3
    db_path = str(tmp_path / "skip_test.db")
    model = FeedbackModel(db_path=db_path)
    model.init_db()

    user_id = "user-skip-filter-test"
    track_to_skip = test_index.tracks[0]["track_id"]

    # Insert a skip into SQLite feedback
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                track_id TEXT,
                action TEXT,
                created_at TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO feedback (user_id, track_id, action, created_at) VALUES (?, ?, 'skip', datetime('now'))",
            (user_id, track_to_skip),
        )
        conn.commit()

    recommender = Recommender(index=test_index, feedback_model=model)
    items, _, _ = recommender.recommend(
        query="calm music", user_id=user_id, mode="familiar", limit=20
    )
    recommended_ids = {it["track_id"] for it in items}
    assert track_to_skip not in recommended_ids
