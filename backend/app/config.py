"""Settings loaded from `backend/.env`."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
"""The `backend/` directory, the base for the database, cache and fixture paths."""


class Settings(BaseSettings):
    """Holds every setting the backend reads from the environment."""

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    gemini_api_key: str = ""
    gemini_grounded_api_key: str = ""
    gemini_model_fast: str = "gemini-3.5-flash-lite"
    gemini_model_smart: str = "gemini-3.8-flash"
    gemini_model_live: str = "gemini-3.8-flash"
    places_api_key: str = ""
    pagespeed_api_key: str = ""
    serpapi_api_key: str = ""
    meta_access_token: str = ""
    meta_ig_user_id: str = ""
    demo_mode: Literal["off", "fixture"] = "off"
    demo_place_id: str = ""
    frontend_origin: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    """Returns the settings, read once from the environment and `.env`."""
    return Settings()
