from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    embed_model_name: str = Field(
        default="sentence-transformers/paraphrase-MiniLM-L6-v2",
        env="EMBED_MODEL_NAME",
    )

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
