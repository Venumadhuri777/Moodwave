# Dataset Specification & Decisions: MTG-Jamendo

## 1. Selected Dataset Source
Moodwave utilizes the **MTG-Jamendo Dataset**, an open-source, large-scale music audio and metadata corpus curated by the **Music Technology Group (MTG) at Universitat Pompeu Fabra (Barcelona)**.
- **GitHub Repository**: [github.com/MTG/mtg-jamendo-dataset](https://github.com/MTG/mtg-jamendo-dataset)
- **Zenodo Archive**: [Zenodo Record 3826813](https://zenodo.org/record/3826813)
- **Target Files**: Tag distribution files and metadata splits (specifically `autotagging_moodtheme.tsv` / `autotagging.tsv` and `raw_metadata.tsv`).

---

## 2. Audio vs. Metadata Scope & Attribute Constraints
- **Metadata and Tags Only**: Moodwave exclusively ingests and operates on track metadata, genre tags, and mood/theme tags.
- **No Acoustic / Spotify Audio Features**: The MTG-Jamendo catalog contains **NO energy, valence, tempo, or danceability values**. Therefore, the intent parsing, filtering, and recommendation layers operate exclusively on mood/theme tags and genre tags. No synthetic energy or valence values are fabricated.
- **No Audio Files**: Audio files (`.mp3` / `.flac`) are **not** downloaded, stored, or processed. The vector representations and semantic IDs are derived entirely from contextual text representations, tag co-occurrences, and multi-label embedding spaces.

---

## 3. Explicit Architecture Decision: No Kaggle Datasets
We made an intentional decision **not** to use ad-hoc Kaggle datasets (such as static Spotify audio feature dumps).
- **Reasoning**:
  1. The problem statement does not require or mandate a Kaggle dataset.
  2. Public Kaggle Spotify dumps are typically stale, heavily duplicated, lack open licensing, and do not provide rich, multi-label semantic mood/theme annotations.
  3. MTG-Jamendo is an established academic benchmark with well-defined splits, rich mood/theme ontologies, and transparent attribution.

---

## 4. Licensing & Attribution
- **Metadata License**: Apache 2.0. Metadata can be freely used, transformed, and distributed with proper attribution.
- **Audio License**: Creative Commons BY-NC-SA 4.0. Because Moodwave utilizes **metadata only**, we strictly operate within the permissive Apache 2.0 metadata provisions while respecting non-commercial academic standards.
- **Mandatory Attribution**: All project deliverables, presentations, READMEs, and hackathon pitch decks must credit the dataset:
  > *Music Technology Group, Universitat Pompeu Fabra. MTG-Jamendo Dataset: An open dataset for music auto-tagging.*

---

## 5. Catalog Context: Jamendo vs. Spotify
Tracks in Moodwave's catalog originate from Jamendo, not Spotify.
- **Why Not the Spotify API?**
  1. **API Restrictions (November 2024)**: Spotify permanently deprecated and closed its core algorithmic endpoints (`/recommendations`, audio features, audio analysis, related artists) to new developer applications.
  2. **Development Mode Constraints (February 11, 2026)**: Spotify tightened developer restrictions requiring developer accounts to hold paid Premium subscriptions, capping development applications to 1 client ID and a maximum of 5 pre-approved Spotify accounts, with search endpoints artificially throttled to 10 results.
- **Algorithmic Parity**:
  The recommender, intent-parsing, and semantic ID quantization methods designed in Moodwave are **completely catalog-agnostic**. The core techniques—language steering, hierarchical semantic ID clustering, familiar vs. non-habitual mode shifts, and explainable scoring—operate identically on any music catalog equipped with textual tags, descriptions, or metadata.

---

## 6. Items to Verify in Part 2
The following items are flagged for verification during **Phase 2 (Data Ingestion & Exploration)**:
1. **`autotagging.tsv` Column Schema**:
   - *To verify in Part 2*: What exact column headers exist in `autotagging_moodtheme.tsv` / `autotagging.tsv` (e.g., `TRACK_ID`, `ARTIST_ID`, `ALBUM_ID`, `TAGS`)?
2. **Track Titles and Artist Names**:
   - *To verify in Part 2*: Are human-readable track titles and artist names bundled directly inside the TSV split files, or are they isolated in the separate `raw_metadata.tsv` / `raw_30s_cleantags.json` dump from the MTG-Jamendo repository?
3. **Contingency Plan**:
   - If track titles and artist names are absent from the split TSVs, the ingestion script will join against `raw_metadata.tsv` from the MTG repository.
   - If additional track metadata or live streaming links are desired, Jamendo's public REST API will be queried using a `JAMENDO_CLIENT_ID` (to be provided in the final phase).
