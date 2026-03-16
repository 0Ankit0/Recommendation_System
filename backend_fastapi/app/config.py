from functools import lru_cache
from typing import Annotated

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Recommendation System API (FastAPI)"
    environment: str = "development"
    database_url: str = "sqlite:///./recommendation.db"
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    access_token_expire_minutes: int = 60
    jwt_secret_key: str = Field(
        default="change-me-in-production",
        min_length=16,
        description="JWT signing key. Must be overridden in production.",
    )
    jwt_algorithm: str = "HS256"


@lru_cache
def get_settings() -> Settings:
    return Settings()


SettingsDep = Annotated[Settings, get_settings]
