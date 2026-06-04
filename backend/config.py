from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    gemini_api_key: str = ""
    model: str = "gemini-1.5-flash"   # free tier, 15 RPM, 1M tokens/day
    max_suggestions: int = 10
    max_file_size_mb: int = 20

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
