from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

        # PostgreSQL
    database_url: str

    # MinIO (S3-compatible object storage)
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket_name: str
    minio_secure: bool = False
