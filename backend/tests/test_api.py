import pytest
from fastapi.testclient import TestClient
from app.config import settings
from app.main import app
from app.middleware import rate_limiter

@pytest.fixture(autouse=True)
def reset_rate_limit():
    rate_limiter.reset()
    yield
    rate_limiter.reset()

def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data_loaded" in data
        assert "feedback_db_ok" in data
        assert "llm_configured" in data
        assert "catalog_size" in data
        assert data["status"] == "ok"
        assert data["data_loaded"] is True
        assert data["catalog_size"] > 0
        assert "X-Request-ID" in response.headers

def test_recommend_valid_query():
    with TestClient(app) as client:
        payload = {
            "query": "calm study lofi",
            "mode": "familiar",
            "user_id": "test-user-12345",
            "limit": 5,
        }
        response = client.post("/v1/recommend", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "intent" in data
        assert data["intent"] is not None
        assert "moods" in data["intent"]
        assert "genres" in data["intent"]
        assert "avoid_genres" in data["intent"]
        assert "confidence" in data["intent"]
        assert data["source"] == "rules"
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) <= 5
        assert data["degraded"] is True
        assert data["degraded_reason"] in ("embedding_unavailable", "placeholder_ranking")

        if data["items"]:
            item = data["items"][0]
            assert "track_id" in item
            assert "title" in item
            assert "artist" in item
            assert "genre" in item
            assert "mood_tags" in item
            assert "explanation" in item
            assert "semantic_id" in item
            assert "track_url" in item

def test_recommend_empty_query():
    with TestClient(app) as client:
        payload = {
            "query": "   ",
            "user_id": "test-user-12345",
        }
        response = client.post("/v1/recommend", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "request_id" in data["error"]

def test_recommend_invalid_mode():
    with TestClient(app) as client:
        payload = {
            "query": "calm study",
            "mode": "invalid_mode",
            "user_id": "test-user-12345",
        }
        response = client.post("/v1/recommend", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"

def test_recommend_control_character():
    with TestClient(app) as client:
        payload = {
            "query": "calm study\x00beat",
            "user_id": "test-user-12345",
        }
        response = client.post("/v1/recommend", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"

def test_catalog_unknown_track():
    with TestClient(app) as client:
        response = client.get("/v1/catalog/nonexistent_track_999999")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"
        assert "request_id" in data["error"]

def test_feedback_success():
    with TestClient(app) as client:
        payload = {
            "user_id": "test-user-12345",
            "track_id": "jamendo_100001",
            "action": "save",
        }
        response = client.post("/v1/feedback", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "recorded"
        assert data["user_id"] == "test-user-12345"
        assert data["track_id"] == "jamendo_100001"
        assert data["action"] == "save"
        assert "timestamp" in data

        # Verify user vector was updated in feedback_model
        user_vec = app.state.feedback_model.get_user_vector("test-user-12345")
        assert user_vec is not None

def test_feedback_invalid_action():
    with TestClient(app) as client:
        payload = {
            "user_id": "test-user-12345",
            "track_id": "jamendo_100001",
            "action": "dislike",
        }
        response = client.post("/v1/feedback", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"

def test_rate_limit_exceeded():
    original_limit = settings.RATE_LIMIT_PER_MINUTE
    settings.RATE_LIMIT_PER_MINUTE = 3
    try:
        with TestClient(app) as client:
            # 3 requests allowed
            for _ in range(3):
                r = client.get("/health")
                assert r.status_code == 200

            # 4th request must be rate limited
            limited_response = client.get("/health")
            assert limited_response.status_code == 429
            assert "Retry-After" in limited_response.headers
            data = limited_response.json()
            assert "error" in data
            assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    finally:
        settings.RATE_LIMIT_PER_MINUTE = original_limit

def test_request_id_header_propagation():
    custom_id = "custom-test-req-id-12345"
    with TestClient(app) as client:
        response = client.get("/health", headers={"X-Request-ID": custom_id})
        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == custom_id
