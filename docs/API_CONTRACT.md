# REST API Contract: Moodwave Backend

Base URL: `http://localhost:8000` (or Android emulator loopback `http://10.0.2.2:8000`)

All responses use standard `application/json` formatting.

---

## 1. Endpoints

### 1.1 Health Check
- **Method / Path**: `GET /health`
- **Description**: Returns backend service status, index readiness, and LLM configuration state.
- **Request**: Empty.
- **Response** (`200 OK`):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "catalog_size": 25000,
  "index_loaded": true,
  "llm_enabled": true
}
```

---

### 1.2 Language-Steered Recommendations
- **Method / Path**: `POST /v1/recommend`
- **Description**: Parses the natural language prompt, determines structured intent (moods, genres, avoid_genres, context, confidence), applies prefix-filtering according to the discovery mode (`familiar` vs. `non_habitual`), and returns 10 recommended tracks with rationales.
- **Important Data Constraint**: The MTG-Jamendo catalog contains NO energy, valence, tempo, or danceability attributes. The intent layer operates exclusively on mood/theme tags and genre tags.
- **Request Body**:
```json
{
  "query": "chill lo-fi beats for late night calculus revision",
  "mode": "familiar",
  "user_id": "anon_student_9021",
  "limit": 10
}
```
*Fields:*
- `query` (string, required): The natural language prompt or mood chip label.
- `mode` (string, optional, default: `"familiar"`): Either `"familiar"` or `"non_habitual"`.
- `user_id` (string, required): Anonymous device/session identifier.
- `limit` (integer, optional, default: `10`): Number of recommendations to return (1-20).

- **Response** (`200 OK`):
```json
{
  "intent": {
    "moods": ["calm", "relaxing"],
    "genres": ["lofi", "ambient"],
    "avoid_genres": [],
    "context": "late night study session",
    "confidence": 0.95
  },
  "source": "llm",
  "items": [
    {
      "track_id": "jamendo_102938",
      "title": "Midnight Desk Clock",
      "artist": "StudyCraft",
      "genre": "lofi",
      "mood_tags": ["relaxing", "calm", "study"],
      "explanation": "Selected for calm study focus with gentle lo-fi progression.",
      "semantic_id": "14.08.31",
      "track_url": "https://jamendo.com/track/102938"
    },
    {
      "track_id": "jamendo_492011",
      "title": "Library Whispers",
      "artist": "Acoustic Rain",
      "genre": "ambient",
      "mood_tags": ["peaceful", "soft", "meditative"],
      "explanation": "Aligns with your quiet revision request using soft ambient acoustic textures.",
      "semantic_id": "14.08.52",
      "track_url": "https://jamendo.com/track/492011"
    }
  ],
  "degraded": false,
  "degraded_reason": null
}
```

- **Degraded Fallback Response** (`200 OK` when LLM is unavailable):
```json
{
  "intent": {
    "moods": ["calm"],
    "genres": ["lofi"],
    "avoid_genres": [],
    "context": "study",
    "confidence": 0.8
  },
  "source": "rules",
  "items": [
    {
      "track_id": "jamendo_102938",
      "title": "Midnight Desk Clock",
      "artist": "StudyCraft",
      "genre": "lofi",
      "mood_tags": ["relaxing", "calm", "study"],
      "explanation": "Matched via rule engine on keywords: 'chill', 'lo-fi', 'study'.",
      "semantic_id": "14.08.31",
      "track_url": "https://jamendo.com/track/102938"
    }
  ],
  "degraded": true,
  "degraded_reason": "Gemini API key not configured. Fallback rule-based parser active."
}
```

---

### 1.3 User Interaction Feedback
- **Method / Path**: `POST /v1/feedback`
- **Description**: Records listener feedback (`skip`, `save`, `replay`) to steer session reranking.
- **Request Body**:
```json
{
  "user_id": "anon_student_9021",
  "track_id": "jamendo_102938",
  "action": "skip"
}
```
*Fields:*
- `user_id` (string, required): Anonymous user identifier.
- `track_id` (string, required): ID of the track interacted with.
- `action` (string, required): One of `"skip"`, `"save"`, or `"replay"`.

- **Response** (`200 OK`):
```json
{
  "status": "recorded",
  "user_id": "anon_student_9021",
  "track_id": "jamendo_102938",
  "action": "skip",
  "timestamp": "2026-11-04T00:15:00Z"
}
```

---

### 1.4 Track Catalog Lookup
- **Method / Path**: `GET /v1/catalog/{track_id}`
- **Description**: Retrieves full metadata for a specific track.
- **Request**: Path parameter `track_id`.
- **Response** (`200 OK`):
```json
{
  "track_id": "jamendo_102938",
  "title": "Midnight Desk Clock",
  "artist": "StudyCraft",
  "album": "Dorm Sessions Vol. 1",
  "genre": "lofi",
  "mood_tags": ["relaxing", "calm", "study"],
  "semantic_id": "14.08.31",
  "duration_seconds": 184,
  "track_url": "https://jamendo.com/track/102938",
  "license": "CC BY-NC-SA 4.0"
}
```

---

## 2. Standard Error Responses & HTTP Status Codes

When an endpoint fails or encounters an unhandled anomaly, it returns a standard JSON error payload:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Field 'action' must be one of: ['skip', 'save', 'replay']",
    "details": null
  }
}
```

### HTTP Status Code Mapping:
- **`200 OK`**: Successful request. Note that LLM service failure still returns `200 OK` with `degraded: true` and `source: "rules"` whenever possible.
- **`400 Bad Request`**: Malformed JSON syntax or invalid query parameters.
- **`422 Unprocessable Entity`**: Request schema validation failure (e.g., missing required `user_id`, or `limit` out of range).
- **`429 Too Many Requests`**: Rate limit exceeded on rapid successive queries.
- **`503 Service Unavailable`**: Fatal upstream unavailability (returned only if both LLM and the rule-based fallback engine are completely unable to serve recommendations).
