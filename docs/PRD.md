# Product Requirements Document (PRD): Moodwave

## 1. Executive Overview
Moodwave is a language-steerable music discovery application designed to match student lifestyle moments with precision, explainability, and steerability. Built as a proof-of-concept hackathon solution for Problem #8, it empowers users to steer discovery through natural text prompts or curated mood chips while offering deliberate control between familiar comfort listening and non-habitual music frontiers.

---

## 2. Target User Persona
- **Primary Persona**: College and university students.
- **Key Use Cases & Moments**:
  - **Study / Deep Focus**: Low-distraction, instrumental, lo-fi, or ambient soundscapes tailored to high-stress exam prep or reading.
  - **Sleep / Wind-Down**: Soothing, low-tempo, minimally percussive sound environments that facilitate relaxation and rest.
  - **Commute / Transit**: Rhythmic, medium-to-high energy beats for morning walks, bus rides, or cycling without high cognitive friction.
- **Pain Point**: Students spend valuable time hunting for background music that fits their exact momentary mental state, only to encounter repetitive algorithmic loops from standard streaming recommendation engines.

---

## 3. Core User Flow
1. **Prompt Entry / Chip Selection**:
   - The user opens the app and either types a natural language request (e.g., *"calm ambient rain sounds for 2 AM math revision"*) or taps a curated mood chip (e.g., `Deep Study`, `Late Night Wind-Down`, `Morning Commute`, `High Energy Rush`).
   - The user selects the exploration mode via a top-level toggle: **Familiar** vs. **Non-habitual**.
2. **Recommendation Presentation**:
   - The backend responds with a curated shelf of **10 tracks**.
   - Each track item card displays:
     - Track Title and Artist Name.
     - Genre and primary Mood/Theme tags.
     - A concise, transparent **one-line explanation** detailing why this specific track satisfies the user's intent and selected mode.
3. **Session Steering & Feedback**:
   - For every track card, the user can take one of three explicit feedback actions:
     - **Skip**: Immediately demotes similar candidates and adjusts session preferences away from this cluster.
     - **Save**: Bookmarks the track locally in the on-device library.
     - **Replay**: Reinforces the track's semantic neighborhood for subsequent recommendations.
   - Dynamic mode toggle switching allows the listener to instantly re-query between comfort listening (**Familiar**) and exploratory discovery (**Non-habitual**).

---

## 4. Scope Boundaries

### In Scope
- Natural language intent parsing (dual path: Gemini LLM structured parsing with automatic rule-based fallback).
- Hierarchical semantic ID quantization index for familiar vs. non-habitual candidate retrieval.
- Jetpack Compose Android client with modern reactive UI.
- On-device Room database caching for offline track viewing and action queuing.
- Degraded mode UI indicators when falling back to rules or offline cache.
- Interactive feedback actions (Skip, Save, Replay) updating session context.

### Out of Scope (Explicitly Excluded)
- **User Login / Authentication**: Anonymous device-level identifiers only; no account sign-in required.
- **In-App Audio Playback**: Audio decoders/players are out of scope; track metadata links directly to open external track URLs (Jamendo).
- **Payments & Subscriptions**: Free open discovery; no monetization layer.
- **Social Features**: No friends lists, sharing feeds, or public profiles.
- **Spotify API Calls**: Absolutely no dependency on the Spotify Web API or Spotify OAuth tokens.

---

## 5. Success Criteria & Judging Rubric Mapping

| Judging Rubric Dimension | Weight | Success Criteria in Moodwave |
| :--- | :---: | :--- |
| **Working End-to-End Demo** | **30 pts** | • Fully operational Android Jetpack Compose client communicating with a running FastAPI backend.<br>• Seamless execution of the core flow: prompt/chip input → 10 track recommendations with one-line rationales → interactive Skip/Save/Replay actions.<br>• Working toggle between "Familiar" and "Non-habitual" discovery modes.<br>• Functional on-device Room caching displaying previously fetched results offline. |
| **Innovation** | **20 pts** | • **Semantic IDs via Hierarchical Quantization**: Structuring catalog embeddings into hierarchical discrete prefix codes ($64 \times 64 \times 64$), enabling mathematical navigation across prefix trees to reliably serve non-habitual discoveries.<br>• **Dual-Path Intent Engine**: Structured schema extraction via LLM paired with an instantaneous rule-based regex fallback.<br>• **Dynamic One-Line Rationales**: Explanations generated directly linking extracted intent attributes (mood, energy, context) to catalog tag signatures. |
| **Measured Result** | **20 pts** | • Rigorous offline evaluation on 200 simulated listeners achieving target **Hit@10** and **NDCG@10** surpassing both baseline models (global popularity and genre-only match).<br>• Intent parsing benchmark evaluating accuracy across 60 hand-labelled benchmark queries on mood, energy, and context.<br>• Verified p95 latency: $<300\text{ ms}$ on the rule path and $<2.0\text{ s}$ on the LLM path. |
| **Reliability & Safety** | **20 pts** | • Zero hard failures: graceful degradation from LLM to rules fallback if the API key is absent, rate-limited, or unavailable, surfaced transparently via degraded UI banners.<br>• Zero PII leakage: LLM receives only prompt text; device/user IDs never leave the local environment.<br>• Offline resilience: Room local cache serves cached recommendations when network connectivity is lost. |
| **Impact & Clarity** | **10 pts** | • Directly solves the repetitive music discovery problem for high-stress student moments (study, sleep, commute).<br>• Transparent, reproducible documentation, clear evaluation scripts, and clean separation of concerns. |
