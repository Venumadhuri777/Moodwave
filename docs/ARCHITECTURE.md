# Architecture & System Design: Moodwave

## 1. System Overview & Component Diagram

```text
+---------------------------------------------------------------------------------------+
|                                    ANDROID APP                                        |
|                                                                                       |
|   +-------------------------------------------------------------------------------+   |
|   |                           Jetpack Compose UI Layer                            |   |
|   |  - Mood Chips  - Search Bar  - Mode Toggle (Familiar/Non-hab)  - Track Cards   |   |
|   |  - One-Line Explanations  - Skip/Save/Replay Buttons  - Degraded Mode Banner  |   |
|   +-------------------------------------------------------------------------------+   |
|                                          |                                            |
|                                          v                                            |
|   +-------------------------------------------------------------------------------+   |
|   |                         MoodwaveViewModel (Stateflow)                         |   |
|   +-------------------------------------------------------------------------------+   |
|                                          |                                            |
|                                          v                                            |
|   +-------------------------------------------------------------------------------+   |
|   |                          MusicRepository (Single Source)                      |   |
|   +-------------------------------------------------------------------------------+   |
|                       |                                       |                       |
|                       v                                       v                       |
|       +-------------------------------+       +-------------------------------+       |
|       |     Room Database (Local)     |       |     Retrofit Client (HTTP)    |       |
|       |  - Tracks Cache               |       |  - /v1/recommend              |       |
|       |  - Offline Feedback Queue     |       |  - /v1/feedback               |       |
|       +-------------------------------+       +-------------------------------+       |
+---------------------------------------------------------------|-----------------------+
                                                                | HTTP / JSON
                                                                v
+---------------------------------------------------------------------------------------+
|                                   FASTAPI BACKEND                                     |
|                                                                                       |
|   +-------------------------------------------------------------------------------+   |
|   |                               API Routes Router                               |   |
|   |     GET /health | POST /v1/recommend | POST /v1/feedback | GET /v1/catalog    |   |
|   +-------------------------------------------------------------------------------+   |
|                                          |                                            |
|                     +--------------------+--------------------+                       |
|                     |                                         |                       |
|                     v                                         v                       |
|   +----------------------------------+      +----------------------------------+      |
|   |          Intent Parser           |      |          Feedback Store          |      |
|   |  (Gemini LLM / Rule Fallback)    |      |  (User session skips/saves/reps) |      |
|   +----------------------------------+      +----------------------------------+      |
|                     |                                         |                       |
|                     +--------------------+--------------------+                       |
|                                          v                                            |
|   +-------------------------------------------------------------------------------+   |
|   |                               Recommender Core                                |   |
|   |  - Prefix Filtering (Semantic IDs: Familiar vs. Non-habitual)                 |   |
|   |  - Vector Cosine Similarity Scoring & Penalty Reranking                       |   |
|   +-------------------------------------------------------------------------------+   |
|                     |                                         |                       |
|                     v                                         v                       |
|   +----------------------------------+      +----------------------------------+      |
|   |        Semantic ID Index         |      |             Explainer            |      |
|   |  (3-level discrete prefix tree)  |      |   (Deterministic 1-line rationale|      |
|   |                                  |      |    linking intent & track tags)  |      |
|   +----------------------------------+      +----------------------------------+      |
+---------------------------------------------------------------------------------------+
              ^                                                 ^
              | (Artifacts: index.pkl, catalog.json)            | (Prompt / Schema)
+-------------|---------------------------------+   +-----------|---------------------+
|      OFFLINE DATA PIPELINE                     |   |   OPTIONAL EXTERNAL LLM SERVICE |
|                                                |   |                                 |
|  - Raw MTG-Jamendo Ingestion (data/raw/)       |   |  - Google Gemini API            |
|  - Tag Embedding Generation                    |   |  - Disabled gracefully when no  |
|  - Hierarchical Vector Quantization (3-level)  |   |    API key is set               |
|  - Serialized Artifacts -> data/processed/     |   |                                 |
+------------------------------------------------+   +---------------------------------+
```

---

## 2. Component Descriptions

### 2.1 Android Application
- **SDK Specifications**:
  - `minSdk`: **26** (Android 8.0 Oreo - guarantees modern java.time, coroutines, and notification channels)
  - `compileSdk`: **35** (Android 15 - latest stable platform SDK)
  - `targetSdk`: **35** (Android 15)
- **Compose UI**: Declarative, responsive UI rendering mood chips (`Study`, `Sleep`, `Commute`), query input, discovery toggle (`Familiar` vs. `Non-habitual`), 10-track feed with one-line rationales, action buttons (`Skip`, `Save`, `Replay`), and degraded-state indicators.
- **ViewModel**: Manages UI state, handles user interaction events, coordinates Coroutines for background tasks, and emits state flows (`Loading`, `Success`, `Error`, `Degraded`).
- **Repository**: Single source of truth. Handles network connectivity, queries Retrofit client, writes responses to the local Room database, and flushes the offline feedback queue.
- **Room Cache**: SQLite-backed local persistence storing tracks, recent searches, and unsent feedback events.
- **Retrofit Client**: Type-safe REST client communicating with the FastAPI backend over HTTP/JSON.

### 2.2 FastAPI Backend
- **API Routes**: Exposes `/health`, `/v1/recommend`, `/v1/feedback`, and `/v1/catalog/{track_id}`.
- **Intent Parser**: Dual-mode engine. Attempts structured JSON schema extraction via Google Gemini LLM; gracefully falls back to deterministic rule-based keyword/regex extraction when the LLM is unconfigured, timed out, or unavailable.
- **Semantic ID Index**: Organizes catalog tracks into a 3-level prefix hierarchy ($64 \times 64 \times 64$ codes). Enables fast partition filtering: familiar mode queries within prefix neighborhoods; non-habitual mode actively branches into disjoint prefixes.
- **Recommender Core**: Combines prefix candidate filtering with dense vector similarity and adjusts scores using user feedback penalties/boosts (e.g., skipped tracks demote clusters).
- **Feedback Store**: Tracks session interactions (skips, saves, replays) mapped to `user_id` to adjust reranking weights.
- **Explainer**: Synthesizes a transparent, concise one-line explanation for each recommended track, directly explaining the link between user intent attributes and track metadata tags.

### 2.3 Offline Data Pipeline (`scripts/`)
- Ingests MTG-Jamendo TSV metadata and tag splits from `data/raw/`.
- Cleans and filters tags to core mood/theme and genre vocabularies.
- Generates dense tag-semantic embeddings.
- Trains a 3-level hierarchical quantizer (64 clusters per level) and assigns a discrete semantic ID (e.g., `12.04.58`) to each track.
- Emits pre-indexed artifacts (`catalog.json`, `semantic_index.pkl`) into `data/processed/`.

### 2.4 Optional LLM Service
- Uses Google Gemini API for zero-shot natural language understanding.
- Operates under strict timeout limits.
- If no `GEMINI_API_KEY` is supplied in backend `.env`, the system automatically switches to the internal rule-based parser without crashing.

---

## 3. End-to-End Request Data Flow

```text
[User Types Query / Selects Chip]
                │
                ▼
1. Android Client dispatches POST /v1/recommend { query, mode, user_id, limit: 10 }
                │
                ▼
2. FastAPI Routes receive payload and forward query to Intent Parser
                │
                ▼
3. Intent Parser:
   ├── Try: Gemini LLM Structured JSON Output (mood, energy, context, genres)
   └── Catch/Fallback: Deterministic Rule-Based Parsing (regex & keyword map)
                │
                ▼
4. Recommender Core retrieves candidate tracks from Semantic ID Index:
   ├── If Mode == "familiar": filter candidates sharing user/intent prefix
   └── If Mode == "non_habitual": filter candidates with intentional prefix divergence
                │
                ▼
5. Reranker scores candidates using embedding cosine similarity and applies
   penalties from Feedback Store (e.g., recent skips penalized, replays boosted)
                │
                ▼
6. Explainer generates a 1-line rationale for each top 10 item:
   "Matches your [mood] [context] prompt with [genre/energy] characteristics."
                │
                ▼
7. FastAPI returns JSON payload:
   { intent, source ("llm"|"rules"), items: [...10 tracks with explanations...], degraded }
                │
                ▼
8. Android Client receives response:
   ├── Writes tracks to Room Local Database
   └── Renders 10 recommendation cards + mode indicator banner in Compose UI
```
