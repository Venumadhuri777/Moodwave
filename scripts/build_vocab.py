#!/usr/bin/env python3
"""Build vocabulary of distinct moods and genres from catalog.csv and standard MTG-Jamendo taxonomies."""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = PROJECT_ROOT / "data" / "processed" / "catalog.csv"
VOCAB_PATH = PROJECT_ROOT / "data" / "processed" / "vocab.json"

# Standard MTG-Jamendo mood/theme tags to ensure comprehensive coverage
STANDARD_MOODS = [
    "action", "adventure", "advertising", "ambient", "background", "ballad",
    "calm", "children", "chill", "christmas", "commercial", "cool", "corporate",
    "dark", "deep", "documentary", "drama", "dramatic", "dream", "driving",
    "emotional", "energetic", "epic", "fast", "film", "focus", "fun", "funny",
    "game", "groovy", "happy", "heavy", "holiday", "hopeful", "horror",
    "inspiring", "instrumental", "love", "meditative", "melancholic", "motivational",
    "movie", "nature", "party", "peaceful", "positive", "relaxing", "retro",
    "romantic", "sad", "sexy", "sleep", "slow", "soft", "soundscape", "space",
    "sport", "study", "summer", "trailer", "travel", "upbeat", "uplifting", "video", "warm"
]

# Standard MTG-Jamendo genres
STANDARD_GENRES = [
    "ambient", "blues", "chillhop", "chillout", "cinematic", "classical",
    "country", "dance", "downtempo", "drone", "electronic", "folk",
    "funk", "hiphop", "house", "indie", "jazz", "latin", "lofi",
    "metal", "orchestral", "piano", "pop", "punk", "reggae", "rock",
    "rnb", "smoothjazz", "soul", "soundtrack", "synthwave", "techno", "trance", "world"
]

def build_or_load_vocab(force: bool = False):
    if not force and VOCAB_PATH.is_file():
        try:
            with open(VOCAB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "moods" in data and "genres" in data and isinstance(data["moods"], list) and isinstance(data["genres"], list):
                # Verify that key moods like happy, sad, romantic are present
                if "happy" in data["moods"] and "sad" in data["moods"]:
                    print(f"[build_vocab] Existing valid vocab.json found at {VOCAB_PATH}")
                    print_top_entries(data["moods"], data["genres"])
                    return data
        except Exception as e:
            print(f"[build_vocab] Existing vocab.json was invalid ({e}), rebuilding...")

    mood_counter = Counter({m: 1 for m in STANDARD_MOODS})
    genre_counter = Counter({g: 1 for g in STANDARD_GENRES})

    if CATALOG_PATH.is_file():
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_genres = row.get("genres", "") or row.get("primary_genre", "")
                for g in raw_genres.split("|"):
                    cleaned_g = g.strip().lower()
                    if cleaned_g:
                        genre_counter[cleaned_g] += 10

                raw_moods = row.get("mood_tags", "")
                for m in raw_moods.split("|"):
                    cleaned_m = m.strip().lower()
                    if cleaned_m:
                        mood_counter[cleaned_m] += 10

    sorted_moods = [item[0] for item in sorted(mood_counter.items(), key=lambda x: (-x[1], x[0]))]
    sorted_genres = [item[0] for item in sorted(genre_counter.items(), key=lambda x: (-x[1], x[0]))]

    vocab_data = {
        "moods": sorted_moods,
        "genres": sorted_genres,
    }

    VOCAB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(VOCAB_PATH, "w", encoding="utf-8") as f:
        json.dump(vocab_data, f, indent=2)

    print(f"[build_vocab] Successfully built and saved vocab.json to {VOCAB_PATH}")
    print_top_entries(sorted_moods, sorted_genres)
    return vocab_data

def print_top_entries(moods, genres):
    print("\n--- Top 20 Mood/Theme Tags ---")
    for i, m in enumerate(moods[:20], 1):
        print(f"{i:2d}. {m}")

    print("\n--- Top 20 Genre Tags ---")
    for i, g in enumerate(genres[:20], 1):
        print(f"{i:2d}. {g}")

if __name__ == "__main__":
    force_rebuild = "--force" in sys.argv
    build_or_load_vocab(force=force_rebuild)
