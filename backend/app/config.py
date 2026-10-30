from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pydantic import SecretStr
from pydantic import Field


class PostgreSQLSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+asyncpg://localhost:localhost@localhost:5432/retail_refund",
        validation_alias="DATABASE_URL",
    )

    echo_sql: bool = False
    pool_size: int = 5
    max_overflow: int = 0

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # database:PostgreSQLSettings= Field(default_factory=PostgreSQLSettings)

    # MinIO (S3-compatible object storage)
    minio_endpoint: str =""
    minio_access_key: str =""
    minio_secret_key: str =""
    minio_bucket_name: str =""
    minio_secure: bool = False

    # Keycloak for autho
    keycloak_issuer: str
    keycloak_jwks_url: str
    keycloak_internal_url: str
    # keycloak_audience: str
    keycloak_client_id: str
    keycloak_client_secret: str | None = None

    # Redis    
    redis_url: str =""


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()