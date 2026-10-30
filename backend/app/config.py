"""
JanMitra Backend – Application Configuration
"""
import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # ── Database ────────────────────────────────────────────────────────────
    database_url: str = "postgresql://janmitra:janmitra_pass@localhost:5432/janmitra_db"

    # ── AI ──────────────────────────────────────────────────────────────────
    gemini_api_key: str = ""
    ai_model: str = "gemini-2.0-flash"

    # ── Government APIs ─────────────────────────────────────────────────────
    data_gov_api_key: str = ""
    api_setu_key: str = ""
    my_scheme_api_key: str = ""

    # ── JWT / Auth ───────────────────────────────────────────────────────────
    jwt_secret: str = "dev_only_secret_replace_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    # ── App ──────────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    environment: str = "development"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ai_available(self) -> bool:
        return bool(self.gemini_api_key)

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
