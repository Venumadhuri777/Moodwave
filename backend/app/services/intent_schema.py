import json
from pathlib import Path
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator
from app.config import settings

VOCAB_CACHE: Optional[dict] = None

def get_vocab() -> dict:
    global VOCAB_CACHE
    if VOCAB_CACHE is not None:
        return VOCAB_CACHE

    vocab_path = Path(settings.DATA_DIR) / "vocab.json"
    if not vocab_path.is_file():
        # Fallback to relative project path
        vocab_path = Path(__file__).resolve().parents[3] / "data" / "processed" / "vocab.json"

    if vocab_path.is_file():
        try:
            with open(vocab_path, "r", encoding="utf-8") as f:
                VOCAB_CACHE = json.load(f)
                return VOCAB_CACHE
        except Exception:
            pass

    return {"moods": [], "genres": []}

def reload_vocab():
    global VOCAB_CACHE
    VOCAB_CACHE = None
    return get_vocab()

class Intent(BaseModel):
    moods: List[str] = Field(default_factory=list)
    genres: List[str] = Field(default_factory=list)
    avoid_genres: List[str] = Field(default_factory=list)
    context: Optional[str] = Field(default=None, max_length=60)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator("moods", mode="before")
    @classmethod
    def validate_moods(cls, v: Any) -> List[str]:
        if not isinstance(v, list):
            return []
        valid_moods = set(get_vocab().get("moods", []))
        cleaned: List[str] = []
        seen = set()
        for item in v:
            if isinstance(item, str):
                val = item.strip().lower()
                if val in valid_moods and val not in seen:
                    seen.add(val)
                    cleaned.append(val)
                    if len(cleaned) == 3:
                        break
        return cleaned

    @field_validator("genres", mode="before")
    @classmethod
    def validate_genres(cls, v: Any) -> List[str]:
        if not isinstance(v, list):
            return []
        valid_genres = set(get_vocab().get("genres", []))
        cleaned: List[str] = []
        seen = set()
        for item in v:
            if isinstance(item, str):
                val = item.strip().lower()
                if val in valid_genres and val not in seen:
                    seen.add(val)
                    cleaned.append(val)
                    if len(cleaned) == 3:
                        break
        return cleaned

    @field_validator("avoid_genres", mode="before")
    @classmethod
    def validate_avoid_genres(cls, v: Any) -> List[str]:
        if not isinstance(v, list):
            return []
        valid_genres = set(get_vocab().get("genres", []))
        cleaned: List[str] = []
        seen = set()
        for item in v:
            if isinstance(item, str):
                val = item.strip().lower()
                if val in valid_genres and val not in seen:
                    seen.add(val)
                    cleaned.append(val)
                    if len(cleaned) == 3:
                        break
        return cleaned

    @field_validator("context", mode="before")
    @classmethod
    def validate_context(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        trimmed = str(v).strip()
        if not trimmed:
            return None
        return trimmed[:60]

    @field_validator("confidence", mode="before")
    @classmethod
    def validate_confidence(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.5
