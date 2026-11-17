from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    mcp_server_url: str = "http://localhost:8070/mcp"
    redis_url: str = "redis://localhost:6380/0"

    openai_api_key: str = ""
    groq_api_key: str = ""

    llm_provider: str = "groq"
    llm_model: str = "openai/gpt-oss-20b"

    fallback_llm_provider: str = "openai"
    fallback_llm_model: str = "gpt-4o-mini"

    image_model: str = "gpt-4o"

    human_review_kill_switch:bool =True

    minio_endpoint: str = ""
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket_name: str = ""
    minio_secure: bool = False

    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_base_url: str = ""
    
    # SQLAlchemy / asyncpg
    sqlalchemy_database_url: str = Field(
        default="",
        validation_alias="DATABASE_URL"
    )

    # Psycopg
    database_url: str = Field(
        default="",
        validation_alias="DATABASE_PSYCOPG_URL"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()


def redis_settings():
    from arq.connections import RedisSettings

    return RedisSettings.from_dsn(get_settings().redis_url)