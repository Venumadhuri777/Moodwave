import re
import unicodedata
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

USER_ID_REGEX = re.compile(r"^[a-zA-Z0-9\-]{8,64}$")

def has_control_characters(s: str) -> bool:
    for ch in s:
        # Check ASCII control characters and unicode category starting with 'C'
        if ord(ch) < 32 or (127 <= ord(ch) <= 159) or unicodedata.category(ch).startswith("C"):
            return True
    return False

# Error Models
class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None
    details: Optional[Any] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail

# Health Check Model
class HealthResponse(BaseModel):
    status: str
    data_loaded: bool
    feedback_db_ok: bool
    llm_configured: bool
    catalog_size: int

from app.services.intent_schema import Intent

# Intent Models (re-export Intent as IntentSchema for backward compatibility)
IntentSchema = Intent

# Recommendation Models
class RecommendItem(BaseModel):
    track_id: str
    title: str
    artist: str
    genre: str
    mood_tags: List[str]
    explanation: str
    semantic_id: str
    track_url: str

class RecommendRequest(BaseModel):
    query: str
    mode: Literal["familiar", "non_habitual"] = "familiar"
    user_id: str
    limit: int = Field(default=10, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        trimmed = v.strip()
        if not (1 <= len(trimmed) <= 300):
            raise ValueError("Query must be between 1 and 300 characters after trimming")
        if has_control_characters(v):
            raise ValueError("Query must not contain control characters")
        return trimmed

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        if not USER_ID_REGEX.match(v):
            raise ValueError("user_id must be 8 to 64 characters, containing only letters, digits, and hyphens")
        return v

class RecommendResponse(BaseModel):
    intent: Optional[IntentSchema] = None
    source: str
    items: List[RecommendItem]
    degraded: bool
    degraded_reason: Optional[str] = None

# Feedback Models
class FeedbackRequest(BaseModel):
    user_id: str
    track_id: str
    action: Literal["skip", "save", "replay"]

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        if not USER_ID_REGEX.match(v):
            raise ValueError("user_id must be 8 to 64 characters, containing only letters, digits, and hyphens")
        return v

class FeedbackResponse(BaseModel):
    status: str
    user_id: str
    track_id: str
    action: str
    timestamp: str

# Catalog Model
class CatalogItemResponse(BaseModel):
    track_id: str
    title: str
    artist: str
    album: Optional[str] = None
    genre: str
    mood_tags: List[str]
    semantic_id: str
    duration_seconds: Optional[int] = None
    track_url: str
    license: Optional[str] = "CC BY-NC-SA 4.0"
