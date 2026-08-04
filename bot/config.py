from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str
    air_labs_api_key: str
    dadata_token: str
    dadata_secret_key: str

    database_url: str = "sqlite+aiosqlite:///./data/bot.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
