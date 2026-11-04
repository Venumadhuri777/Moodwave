# Moodwave Backend Service

FastAPI-based REST backend for language-steerable music discovery.

---

## 1. Quickstart Run Instructions

### Option A: Using the Run Scripts (Recommended)

**macOS / Linux:**
```bash
./scripts/run_backend.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\run_backend.ps1
```

Each script automatically:
1. Creates a virtual environment in `backend/.venv` if it doesn't already exist.
2. Installs or verifies all dependencies from `backend/requirements.txt`.
3. Starts the Uvicorn server on `http://0.0.0.0:8000` from the `backend/` directory.

---

### Option B: Manual Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate    # On Windows: .venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## 2. Environment Variables

Configure environment variables via `backend/.env` (copy from `backend/.env.example`):

| Variable | Default | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | `""` | Optional Google Gemini API key for zero-shot intent parsing. |
| `GEMINI_MODEL` | `""` | Optional model name from Google AI Studio. |
| `CORS_ORIGINS` | `"*"` | Allowed CORS origins for local development. |
| `RATE_LIMIT_PER_MINUTE` | `60` | In-memory client IP rate limit per minute. |
| `DATA_DIR` | `<root>/data/processed` | Path to processed dataset files. |
| `FEEDBACK_DB_PATH` | `<root>/data/feedback.db` | SQLite database path for feedback interactions. |

---

## 3. Endpoints Overview

- `GET /health`: Health check and catalog/database readiness.
- `POST /v1/recommend`: Natural language recommendation engine.
- `POST /v1/feedback`: User session feedback (`skip`, `save`, `replay`).
- `GET /v1/catalog/{track_id}`: Track metadata lookup.
- `GET /docs`: Interactive Swagger OpenAPI documentation.

---

## 4. Running Tests

Run the test suite from the project root:
```bash
./backend/.venv/bin/pytest backend/tests/test_api.py -v
```
