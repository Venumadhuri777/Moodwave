import os
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root: /Users/.../Moodwave (2 levels above backend/app)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = ""
    CORS_ORIGINS: Union[str, List[str]] = "*"
    RATE_LIMIT_PER_MINUTE: int = 60
    DATA_DIR: str = str(PROJECT_ROOT / "data" / "processed")
    FEEDBACK_DB_PATH: str = str(PROJECT_ROOT / "data" / "feedback.db")

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / "backend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
