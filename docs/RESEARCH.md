# Research Notes: Language Steering, Semantic IDs & Reliability

## 1. Spotify Web API Landscape & Strategic Pivot
- **November 2024 Deprecation**: Spotify deprecated and locked down the core endpoints that powered historical recommender projects:
  - `GET /v1/recommendations` (seed-based algorithmic generator)
  - `GET /v1/audio-features` (danceability, valence, acousticness, tempo, etc.)
  - `GET /v1/audio-analysis`
  - `GET /v1/artists/{id}/related-artists`
- **February 11, 2026 Developer Policy**:
  - Requires developers to maintain an active paid Spotify Premium subscription.
  - Enforces a limit of one client ID per developer account.
  - Restricts application development mode to a maximum of 5 manually whitelisted Spotify user IDs.
  - Search queries are capped at 10 returned items.
- **Architectural Decision**:
  Moodwave is completely decoupled from Spotify tokens and credentials. Our architecture demonstrates that modern semantic discovery and language steerability are model- and catalog-independent, relying on open metadata standards (MTG-Jamendo) and standalone vector quantization.

---

## 2. Semantic IDs via Hierarchical Quantization
Traditional recommender systems rely on either discrete collaborative filtering IDs (which cannot express semantic similarity) or continuous high-dimensional vector embeddings (which require computationally heavy approximate nearest neighbor search and do not cleanly demarcate categorical exploration boundaries).

### Hierarchical Vector Quantization Design
- **Structure**: Continuous track embeddings (derived from tag semantics and textual profiles) are quantized into a 3-level hierarchical code:
  $$\text{Semantic ID} = [c_1] . [c_2] . [c_3]$$
  where each code level $c_l \in \{0, 1, \dots, 63\}$ (64 discrete cluster centroids per level, totaling $64^3 = 262,144$ possible leaves).
- **Prefix Properties**:
  - **Level 1 Prefix ($c_1$)**: Macro vibe / overarching genre family (e.g., electronic vs. acoustic ambient).
  - **Level 2 Prefix ($c_1.c_2$)**: Sub-genre and energy band (e.g., lo-fi chillhop vs. industrial ambient).
  - **Level 3 Code ($c_1.c_2.c_3$)**: Specific stylistic and emotional nuance.
- **Steering Discovery (Familiar vs. Non-habitual)**:
  - **Familiar Mode**: Retrieves candidates sharing the Level 1 and Level 2 prefixes ($c_1.c_2$) matching the user's historical preferences and query centroid, optimizing for immediate comfort and high alignment.
  - **Non-habitual Mode**: Constrains retrieval to candidates that match the query intent's mood while deliberately enforcing a **prefix divergence** ($c_1^{\text{item}} \neq c_1^{\text{user}}$ or $c_2^{\text{item}} \neq c_2^{\text{user}}$). This guarantees the recommendation introduces fresh sonic structures rather than circling known clusters.
- *To verify*: Computational overhead and training convergence speed of 3-level Hierarchical K-Means vs. Residual Vector Quantization (RVQ) on the MTG-Jamendo metadata subset.

---

## 3. Dual-Path Intent Parsing
Natural language inputs from students (e.g., *"give me soft rainy instrumentals for calculus cramming"*) must be translated into structured retrieval parameters.

- **Primary Path: Structured LLM Extraction**:
  - Uses Google Gemini API with a deterministic JSON schema.
  - Output fields: `mood` (e.g., calm, dark, melancholic), `energy` (low, medium, high), `context` (study, sleep, commute), and `genres` (array of inferred tags).
- **Secondary Path: Deterministic Rule-Based Fallback**:
  - Implemented with lightweight regex patterns and keyword dictionaries mapping common student phrases (e.g., "study", "cram", "sleep", "gym", "chill") directly to canonical tags and energy levels.
  - Executed automatically when:
    - No `GEMINI_API_KEY` is configured.
    - LLM network call times out ($>1.5\text{ s}$).
    - Upstream service returns HTTP 429 or 503.
- *To verify*: Latency variance and token consumption profiles across candidate Gemini model versions.

---

## 4. Reliability & Fault-Tolerance Engineering
Music listening scenarios (especially mobile commutes or dorm rooms with spotty Wi-Fi) demand resilience:
1. **On-Device Offline Room Cache**:
   - Every recommendation response is cached locally on the Android device via Room.
   - If network requests fail, the client immediately serves cached tracks annotated with a `"Cached Offline"` indicator.
2. **Degraded Mode Banners**:
   - The UI surfaces subtle, honest status chips when running in fallback states:
     - `Mode: Rule-Based (LLM offline)`
     - `Mode: Offline Cache`
3. **Asynchronous Feedback Queue**:
   - User interactions (Skip, Save, Replay) executed while offline are stored in a local SQLite/Room queue and flushed back to the server upon reconnection.
- *To verify*: Conflict resolution policy if an offline-queued action references a track pruned from the backend's active cache.
