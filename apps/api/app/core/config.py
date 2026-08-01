from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(
        default="postgresql+psycopg://undernight:undernight_dev_password@localhost:5432/undernight",
        alias="DATABASE_URL",
    )
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    cors_origins: str = Field(
        default="http://localhost:19006,http://localhost:8081,exp://127.0.0.1:8081",
        alias="CORS_ORIGINS",
    )
    consumption_units_low: int = Field(default=1, alias="CONSUMPTION_UNITS_LOW")
    consumption_units_medium: int = Field(default=2, alias="CONSUMPTION_UNITS_MEDIUM")
    consumption_units_high: int = Field(default=3, alias="CONSUMPTION_UNITS_HIGH")


    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    ollama_base_url: str = Field(
        default="http://host.docker.internal:11434",
        alias="OLLAMA_BASE_URL",
    )
    ollama_model: str = Field(default="qwen3:4b", alias="OLLAMA_MODEL")
    ollama_timeout_seconds: float = Field(default=120, alias="OLLAMA_TIMEOUT_SECONDS")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def consumption_units(self) -> dict[str, int]:
        return {
            "low": self.consumption_units_low,
            "medium": self.consumption_units_medium,
            "high": self.consumption_units_high,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
