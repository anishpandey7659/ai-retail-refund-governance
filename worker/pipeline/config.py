import os
from functools import lru_cache

from pydantic import BaseModel

class Settings(BaseModel):
    mcp_server_url: str = os.getenv("MCP_SERVER_URL", "http://localhost:8070/mcp")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6380/0")
    
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")

    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")  
    llm_model: str = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")  

    fallback_llm_provider: str = os.getenv("FALLBACK_LLM_PROVIDER", "openai")
    fallback_llm_model: str = os.getenv("FALLBACK_LLM_MODEL", "gpt-4o-mini")

    database_url: str = os.getenv("DATABASE_PSYCOPG_URL", "postgresql://anish:pandey@127.0.0.1:5432/retail-refund")

@lru_cache
def get_settings() -> Settings:
    return Settings()


def redis_settings():
    from arq.connections import RedisSettings

    return RedisSettings.from_dsn(get_settings().redis_url)