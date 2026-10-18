from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MEMORA_", extra="ignore")

    app_name: str = "Memora"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://memora:memora@localhost:5432/memora"


@lru_cache
def get_settings() -> Settings:
    return Settings()
