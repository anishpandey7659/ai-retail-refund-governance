import json

import pytest
from langchain_core.messages import AIMessage
from pydantic import ValidationError

from worker.pipeline import llm as llm_module
from worker.pipeline.config import get_settings
from worker.pipeline.mock_llm import (
    MissingMockResponseError,
    MockLLM,
    MockLLMFailure,
)
from worker.pipeline.nodes import base


def test_scenario_response_takes_priority_over_agent_default():
    llm = MockLLM(
        "intake",
        scenario="case-a",
        agent_responses={
            "intake": {
                "status": "missing_info",
                "missing_fields": ["item"],
                "notes": "Agent-specific response.",
            }
        },
        scenario_responses={
            "case-a": {
                "intake": {
                    "status": "match",
                    "missing_fields": [],
                    "notes": "Scenario-specific response.",
                }
            }
        },
    ).with_structured_output(base.IntakeResult)

    result = llm.invoke("intake prompt")

    assert result.status == "match"
    assert result.notes == "Scenario-specific response."


def test_agent_specific_response_is_used_when_scenario_has_no_override():
    llm = MockLLM(
        "intake",
        scenario="case-b",
        agent_responses={
            "intake": {
                "status": "missing_info",
                "missing_fields": ["item"],
                "notes": "Agent-specific response.",
            }
        },
    ).with_structured_output(base.IntakeResult)

    assert llm.invoke("prompt").status == "missing_info"


def test_structured_output_uses_pydantic_validation():
    llm = MockLLM(
        "intake",
        scenario="case-a",
        agent_responses={"intake": {"status": "unknown", "notes": "invalid"}},
    ).with_structured_output(base.IntakeResult)

    with pytest.raises(ValidationError):
        llm.invoke("prompt")


def test_simulated_failure_raises_explicit_error():
    llm = MockLLM(
        "intake",
        scenario="case-a",
        agent_responses={"intake": {"$error": "Provider timed out."}},
    )

    with pytest.raises(MockLLMFailure, match="Provider timed out"):
        llm.invoke("prompt")


def test_raw_image_response_is_returned_as_ai_message():
    llm = MockLLM(
        "image",
        scenario="case-a",
        agent_responses={"image": {"plausible": True, "confidence": 0.9}},
    )

    response = llm.invoke("vision prompt")

    assert isinstance(response, AIMessage)
    assert json.loads(response.content) == {"plausible": True, "confidence": 0.9}


def test_mock_and_replay_routers_do_not_construct_live_clients(
    monkeypatch,
    configure_llm,
    replay_file,
):
    def reject_live_provider(*args, **kwargs):
        pytest.fail("A non-live mode attempted to construct a provider client.")

    monkeypatch.setattr(llm_module, "init_chat_model", reject_live_provider)

    configure_llm(mode="mock", scenario="low_risk")
    mocked = llm_module.init_chat(base.IntakeResult, agent="intake").invoke("prompt")
    assert mocked.status == "match"
    assert isinstance(llm_module.image_model().invoke("prompt"), AIMessage)

    configure_llm(
        mode="replay",
        scenario="low_risk",
        replay_file=str(replay_file),
    )
    replayed = llm_module.init_chat(base.IntakeResult, agent="intake").invoke("prompt")
    assert replayed.status == "match"
    assert isinstance(llm_module.image_model().invoke("prompt"), AIMessage)


def test_replay_requires_file_and_missing_responses_fail_closed(
    configure_llm,
    monkeypatch,
    tmp_path,
):
    configure_llm(mode="replay")
    with pytest.raises(RuntimeError, match="LLM_REPLAY_FILE"):
        llm_module.init_chat(base.IntakeResult, agent="intake")
    with pytest.raises(RuntimeError, match="LLM_REPLAY_FILE"):
        llm_module.image_model()

    replay_path = tmp_path / "incomplete.json"
    replay_path.write_text(
        json.dumps(
            {
                "scenarios": {
                    "low_risk": {
                        "intake": {
                            "status": "match",
                            "missing_fields": [],
                            "notes": "Recorded.",
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    configure_llm(mode="replay", replay_file=str(replay_path))
    with pytest.raises(MissingMockResponseError, match="policy"):
        llm_module.init_chat(base.PolicyResult, agent="policy").invoke("prompt")


def test_mock_router_uses_schema_agent_name_when_not_explicit(configure_llm):
    configure_llm(mode="mock", scenario="low_risk")

    result = llm_module.init_chat(base.IntakeResult).invoke("prompt")

    assert result.status == "match"


def test_invalid_mode_is_rejected_by_settings(configure_llm, monkeypatch):
    configure_llm(mode="unexpected")
    get_settings.cache_clear()

    with pytest.raises(ValidationError):
        get_settings()
