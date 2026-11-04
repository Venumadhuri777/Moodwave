# Moodwave 🌊🎶
> Spotify-style language-steerable music discovery for moments that matter.

Moodwave is a hackathon project built for **Problem #8: Spotify-style Language-Steerable Discovery**. It allows listeners to navigate and steer their music discovery experience using natural language requests (or curated mood chips) with transparent, one-line rationales for every recommendation.

---

## 1. Problem Statement
Traditional music streaming recommendation systems are largely passive and habit-reinforcing. They pigeonhole users into repetitive algorithmic feedback loops based on broad historical listening patterns. When users need music for a specific, nuanced moment—such as late-night exam cramming, deep sleep induction, or a focused morning commute—they must either spend significant effort manually constructing playlists or rely on generic genre shelves.

Furthermore, conventional recommender interfaces lack intuitive **steerability**: users cannot easily request variations, specify situational contexts, or explicitly explore outside their habitual listening comfort zones without completely corrupting their user profile.

**Moodwave solves this by:**
1. Providing **natural language steering**: Users express their desired vibe or situation (e.g., *"upbeat lo-fi for morning walk without harsh percussion"*), which is translated into structured intents.
2. Enabling **hierarchical discovery modes**: A discovery toggle switches between **Familiar** (close to habitual preference) and **Non-habitual** (exploring novel clusters with different semantic prefixes).
3. Delivering **explainable recommendations**: Every single track is served with an immediate, one-line rationale explaining why it was chosen.
4. Implementing a **resilient hybrid architecture**: An LLM-powered structured extraction pipeline with an ultra-fast rule-based fallback, supported by on-device offline caching.

---

## 2. How to Run
<!-- To be filled in Part 10 -->
To be filled in Part 10.

---

## 3. Folder Map

```text
.
├── docs/                     # Specifications, architecture, research & evaluation documentation
│   ├── README.md             # Project overview and directory structure
│   ├── PRD.md                # Product requirements document & judging rubric mapping
│   ├── DATASET.md            # Dataset selection, licensing, and schema verification notes
│   ├── RESEARCH.md           # API constraints, semantic IDs, and technical findings
│   ├── ARCHITECTURE.md       # High-level architecture, component definitions, and data flow
│   ├── API_CONTRACT.md       # REST API endpoint definitions, payloads, and error contracts
│   ├── EVAL_PLAN.md          # Frozen evaluation protocol, metrics, and proxy benchmarks
│   ├── TASKS.md              # 10-phase task checklist
│   ├── SECURITY_PRIVACY.md   # Data privacy boundaries and threat mitigation
│   └── CREDENTIALS.md        # Optional external credential placeholders
├── backend/                  # FastAPI backend service
│   └── .env.example          # Environment variable template
├── android/                  # Android client application (Jetpack Compose UI)
│   └── local.properties.example # Android SDK configuration template
├── scripts/                  # Offline preprocessing, quantization, and evaluation scripts
├── data/
│   ├── raw/                  # Raw dataset files (.gitkeep, uncommitted)
│   └── processed/            # Quantized indices, embeddings, and metadata (.gitkeep, uncommitted)
└── .gitignore                # Git exclusion rules for secrets, builds, and data artifacts
```
