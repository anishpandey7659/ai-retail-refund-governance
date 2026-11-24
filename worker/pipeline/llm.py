from functools import lru_cache
from typing import cast

from langchain.chat_models import init_chat_model
from langchain_core.language_models import LanguageModelInput
from langchain_core.runnables import Runnable
from pydantic import BaseModel

from worker.pipeline.config import get_settings
from worker.pipeline.mock_llm import DEFAULT_SCENARIO_RESPONSES, MockLLM


def init_chat[OutputT: BaseModel](
    schema: type[OutputT],
    temperature: float = 0.0,
    *,
    agent: str | None = None,
) -> Runnable[LanguageModelInput, OutputT]:
    settings = get_settings()
    if settings.llm_mode == "live":
        chain = _live_chat(
            schema,
            temperature,
            settings.llm_model,
            settings.llm_provider,
            settings.groq_api_key,
            settings.openai_api_key,
            settings.fallback_llm_model,
            settings.fallback_llm_provider,
        )
        return cast(Runnable[LanguageModelInput, OutputT], chain)

    agent_name = agent or schema.__name__.removesuffix("Result").lower()
    if settings.llm_mode == "replay":
        if not settings.llm_replay_file:
            raise RuntimeError("LLM_REPLAY_FILE must be set when LLM_MODE=replay.")
        return cast(
            Runnable[LanguageModelInput, OutputT],
            MockLLM(
                agent_name,
                scenario=settings.llm_scenario,
                schema=schema,
                replay_file=settings.llm_replay_file,
            ),
        )

    return cast(
        Runnable[LanguageModelInput, OutputT],
        MockLLM(
            agent_name,
            scenario=settings.llm_scenario,
            schema=schema,
            scenario_responses=DEFAULT_SCENARIO_RESPONSES,
        ),
    )


@lru_cache(maxsize=16)
def _live_chat(
    schema: type[BaseModel],
    temperature: float,
    model: str,
    provider: str,
    groq_api_key: str,
    openai_api_key: str,
    fallback_model: str,
    fallback_provider: str,
) -> Runnable:
    api_keys = {"groq": groq_api_key, "openai": openai_api_key}
    primary_llm = init_chat_model(
        model=model,
        model_provider=provider,
        api_key=api_keys[provider.lower()],
        temperature=temperature,
    ).with_structured_output(schema)
    fallback_llm = init_chat_model(
        model=fallback_model,
        model_provider=fallback_provider,
        api_key=api_keys[fallback_provider.lower()],
        temperature=temperature,
    ).with_structured_output(schema)
    return primary_llm.with_fallbacks([fallback_llm])


def image_model(temperature: float = 0.0) -> Runnable:
    settings = get_settings()
    if settings.llm_mode == "replay":
        if not settings.llm_replay_file:
            raise RuntimeError("LLM_REPLAY_FILE must be set when LLM_MODE=replay.")
        return MockLLM(
            "image",
            scenario=settings.llm_scenario,
            replay_file=settings.llm_replay_file,
        )
    if settings.llm_mode == "mock":
        return MockLLM(
            "image",
            scenario=settings.llm_scenario,
            scenario_responses=DEFAULT_SCENARIO_RESPONSES,
        )
    return _live_image_model(
        temperature,
        settings.image_model,
        settings.fallback_llm_provider,
        settings.groq_api_key,
        settings.openai_api_key,
    )


@lru_cache(maxsize=16)
def _live_image_model(
    temperature: float,
    model: str,
    provider: str,
    groq_api_key: str,
    openai_api_key: str,
) -> Runnable:
    api_keys = {"groq": groq_api_key, "openai": openai_api_key}
    provider = provider.lower()
    return init_chat_model(
        model=model,
        model_provider=provider,
        api_key=api_keys[provider],
        temperature=temperature,
    )