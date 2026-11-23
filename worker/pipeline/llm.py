from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.runnables import Runnable
from worker.pipeline.config import get_settings

from typing import TypeVar, cast
from pydantic import BaseModel
from langchain_core.language_models import LanguageModelInput
OutputT = TypeVar("OutputT", bound=BaseModel)

@lru_cache(maxsize=4)
def init_chat(
    schema: type[OutputT],
    temperature: float = 0.0,
) -> Runnable[LanguageModelInput, OutputT]:
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
    ).with_structured_output(schema)

    fallback_llm = init_chat_model(
        model=settings.fallback_llm_model,
        model_provider=settings.fallback_llm_provider,
        api_key=api_keys[settings.fallback_llm_provider.lower()],
        temperature=temperature,
    ).with_structured_output(schema)

    chain = primary_llm.with_fallbacks([fallback_llm])
    return cast(Runnable[LanguageModelInput, OutputT], chain)


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