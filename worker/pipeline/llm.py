from functools import lru_cache
from langchain.chat_models import init_chat_model
from langchain_core.runnables import Runnable
from worker.pipeline.config import get_settings
from typing import Literal
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

class IntakeVerdict(BaseModel):
    """Intake Agent verdict on a return request."""

    status: Literal["match", "mismatch", "missing_info"] = Field(
        description="match = consistent; mismatch = clear contradiction; missing_info = vague but not contradictory"
    )
    missing_fields: list[str] = Field(
        description="Short names of missing info, e.g. 'affected_part'. Empty list unless status is missing_info."
    )
    notes: str = Field(
        description="1-2 sentences citing specific evidence from the input."
    )


@lru_cache(maxsize=4)
def init_chat(
    temperature: float = 0.0,
) -> Runnable:
    settings = get_settings()
    primary_llm = init_chat_model(
        model=settings.llm_model,
        model_provider=settings.llm_provider,
        temperature=temperature,
    )

    fallback_llm = init_chat_model(
        model=settings.fallback_llm_model,
        model_provider=settings.fallback_llm_provider,
        temperature=temperature,
    )

    return primary_llm.with_fallbacks([fallback_llm])
