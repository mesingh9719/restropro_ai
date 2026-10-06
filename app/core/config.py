"""Environment-backed settings for the stateless AI service."""
import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class Settings(BaseModel):
    environment: Literal["development", "test", "production"] = "development"
    ai_provider: Literal["sarvam"] = "sarvam"
    sarvam_api_key: str = ""
    sarvam_api_base_url: str = "https://api.sarvam.ai"
    sarvam_model: str = "sarvam-105b"
    sarvam_timeout_seconds: float = Field(default=32, ge=5, le=40)
    internal_ai_service_token: str = ""
    log_level: str = "INFO"


def get_settings() -> Settings:
    # Read on demand so a rotated service token takes effect without stale caching.
    return Settings(
        environment=os.getenv("APP_ENV", "development"),
        ai_provider=os.getenv("AI_PROVIDER", "sarvam"),
        sarvam_api_key=os.getenv("SARVAM_API_KEY", ""),
        sarvam_api_base_url=os.getenv("SARVAM_API_BASE_URL", os.getenv("SARVAM_API_URL", "https://api.sarvam.ai")),
        sarvam_model=os.getenv("SARVAM_MODEL", "sarvam-105b"),
        sarvam_timeout_seconds=os.getenv("SARVAM_TIMEOUT_SECONDS", "32"),
        internal_ai_service_token=os.getenv("INTERNAL_AI_SERVICE_TOKEN", ""),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
