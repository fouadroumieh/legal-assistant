# docapi/config.py (Pydantic v2)
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # env names mapped explicitly
    documents_table: str = Field(default="", env="DOCUMENTS_TABLE")
    docs_bucket: str = Field(default="", env="DOCS_BUCKET")
    nlp_url: str = Field(default="", env="NLP_URL")

    # region fallbacks
    bucket_region: str = Field(default="", env="DOCS_BUCKET_REGION")
    aws_region: str = Field(default="", env="AWS_REGION")
    aws_default_region: str = Field(default="", env="AWS_DEFAULT_REGION")

    # pydantic-settings config
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    @property
    def region(self) -> str:
        return (
            self.bucket_region
            or self.aws_region
            or self.aws_default_region
            or "eu-central-1"
        )

    @property
    def docs_bucket_region(self) -> str:
        return self.region


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # loads from env
