# Moodwave Project Tasks Checklist

- [x] **Phase 1: Project Setup, Documentation & Architecture Baseline**
  - [x] Initialize repository structure (`/docs`, `/backend`, `/android`, `/scripts`, `/data/raw`, `/data/processed`).
  - [x] Author core documentation (`README.md`, `PRD.md`, `DATASET.md`, `RESEARCH.md`, `ARCHITECTURE.md`, `API_CONTRACT.md`, `EVAL_PLAN.md`, `SECURITY_PRIVACY.md`, `CREDENTIALS.md`).
  - [x] Set up environment configurations (`.env.example`, `local.properties.example`, `.gitignore`).

- [x] **Phase 2: Data Sourcing, Exploration & MTG-Jamendo Ingestion**
  - [x] Download and inspect MTG-Jamendo metadata and tag TSVs into `data/raw/`.
  - [x] Verify column names and presence of track titles/artists in TSVs.
  - [x] Filter catalog to mood/theme and genre tags; discard audio references.
  - [x] Generate clean intermediate dataset artifacts.

- [x] **Phase 3: Offline Data Pipeline, Embeddings & Semantic ID Quantization**
  - [x] Build tag/mood textual representation vectors.
  - [x] Implement hierarchical vector quantization ($64 \times 64 \times 64$, 3 levels).
  - [x] Compute discrete semantic IDs for each track in catalog.
  - [x] Export indexed catalog and prefix search trees to `data/processed/`.

- [x] **Phase 4: Intent Parsing Engine (Gemini LLM & Rule-Based Fallback)**
  - [x] Implement structured Gemini JSON schema extractor for moods, genres, avoid_genres, context.
  - [x] Implement fast, deterministic regex/dictionary rule-based fallback parser.
  - [x] Implement fallback triggers for missing key, timeout, or API error.
  - [x] Validate parser output schemas against contract definitions.

- [x] **Phase 5: Fast Recommender Core (Prefix Filtering, Scoring & Reranking)**
  - [x] Implement Familiar mode retrieval (candidate filtering by shared semantic prefix).
  - [x] Implement Non-habitual mode retrieval (candidate filtering by prefix divergence).
  - [x] Implement cosine similarity ranking and session feedback penalties/boosts (Skip/Save/Replay).
  - [x] Implement deterministic one-line rationale explainer.

- [x] **Phase 6: Android Project Setup, Networking & Health-Check**
  - [x] Set up Android Gradle project in `/android` (Kotlin, Jetpack Compose, Material 3, minSdk 26).
  - [x] Configure dependencies via Gradle version catalog (`libs.versions.toml`).
  - [x] Implement Retrofit ApiService and kotlinx.serialization DTOs.
  - [x] Build NetResult sealed wrapper with category error mapping.
  - [x] Build HealthViewModel and HomeScreen health check card.
  - [x] Implement build scripts and unit tests with MockWebServer.

- [/] **Phase 7: Android Data Layer (Room, Repositories, WorkManager Sync)**
  - [/] Update `libs.versions.toml` with WorkManager and room-testing artifacts.
  - [/] Update `app/build.gradle.kts` with new dependencies and KSP room schema export arg.
  - [/] Replace `AppDatabase.kt` with 5 full entities and 5 DAOs.
  - [/] Add `JsonConverters.kt` for kotlinx.serialization type converters.
  - [/] Define domain models: `Mode`, `FeedbackAction`, `RecommendationState`.
  - [/] Implement `RecommendationRepository` with 7-day stale cache flow.
  - [/] Implement `FeedbackRepository` with offline-first DB + background sync.
  - [/] Implement `FeedbackSyncWorker` (WorkManager CoroutineWorker, 15 min periodic).
  - [/] Implement `SavedRepository` and `RecentQueriesRepository`.
  - [/] Implement `PrivacyLogRepository` and `UserIdentity` (DataStore UUID).
  - [/] Update `AppContainer.kt` and `MoodwaveApplication.kt` to wire all repositories.
  - [/] Add JVM unit tests covering cache, network, sync, and privacy invariants.

- [/] **Phase 8: Android Jetpack Compose UI & Interactive Experience**
  - [/] Build interactive Compose UI: search field, mood chips (Calm, Focus, Energetic, Happy, Sad, Romantic, Dreamy).
  - [/] Implement Familiar vs. Non-habitual discovery toggle.
  - [/] Render 10 track recommendation cards with dynamic one-line explanations.
  - [/] Add interactive Skip, Save, Replay controls.
  - [/] Surface offline, degraded, rate-limited, and error banners.
  - [/] Add Settings debug screen for backend URL and clear local data.


- [/] **Phase 9: Failure handling, safety rules, and tests**
  - [ ] Build interactive Compose UI: search bar, mood chips (`Study`, `Sleep`, `Commute`).
  - [ ] Implement "Familiar" vs. "Non-habitual" discovery toggle.
  - [ ] Render 10 track recommendation cards with dynamic one-line explanations.
  - [ ] Add interactive Skip, Save, Replay controls.
  - [ ] Surface degraded mode / offline cache banner indicators.

- [ ] **Phase 10: End-to-End Integration, Polish, Verification & Demo Run**
  - [ ] End-to-end integration test connecting Android client with FastAPI backend.
  - [ ] Verify complete user flow across Familiar and Non-habitual modes with offline fallback.
  - [ ] Document final execution instructions in `docs/README.md`.
  - [ ] Prepare pitch materials, proxy evaluation disclosures, and demo scripts.
