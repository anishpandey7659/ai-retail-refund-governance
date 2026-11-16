from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.runnables import Runnable

from worker.pipeline.config import get_settings
from worker.pipeline.nodes.base import IntakeVerdict




@lru_cache(maxsize=4)
def init_chat(
    temperature: float = 0.0,
) -> Runnable:
    settings = get_settings()

    api_keys = {
        "groq": settings.groq_api_key,
        "openai": settings.openai_api_key,
    }

    primary_llm = init_chat_model(
        model=settings.llm_model,
        model_provider=settings.llm_provider,
        api_key=api_keys[settings.llm_provider.lower()],
        temperature=temperature,
    )

    fallback_llm = init_chat_model(
        model=settings.fallback_llm_model,
        model_provider=settings.fallback_llm_provider,
        api_key=api_keys[settings.fallback_llm_provider.lower()],
        temperature=temperature,
    )

    return primary_llm.with_fallbacks([fallback_llm])


@lru_cache(maxsize=4)
def image_model(
    temperature: float = 0.0,
) -> Runnable:
    settings = get_settings()

    api_keys = {
        "groq": settings.groq_api_key,
        "openai": settings.openai_api_key,
    }

    provider = settings.fallback_llm_provider.lower()

    llm = init_chat_model(
        model=settings.image_model,
        model_provider=provider,
        api_key=api_keys[provider],
        temperature=temperature,
    )

    return llm