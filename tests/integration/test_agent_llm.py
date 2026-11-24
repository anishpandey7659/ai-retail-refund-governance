import asyncio
import io

import pytest
from PIL import Image
from pydantic import ValidationError

from ml import image_service
from tests.fixtures.return_cases import make_case
from worker.pipeline.nodes import agents, base


def test_intake_agent_executes_with_structured_mock(configure_llm):
    configure_llm(mode="mock", scenario="low_risk")
    case = make_case("low_risk")

    result = asyncio.run(agents.intake(case))

    assert isinstance(result, base.IntakeResult)
    assert result.status == "match"
    assert case.agent_results["intake"].output == result


def test_behavior_agent_validates_only_its_generated_explanation(
    configure_llm,
    stub_external_services,
):
    configure_llm(mode="mock", scenario="low_risk")
    case = make_case("low_risk")

    result = asyncio.run(agents.behavior(case))

    assert isinstance(result, base.BehaviorResult)
    assert result.risk_score < 0.15
    assert result.summary
    assert case.agent_results["behavior"].error is None


def test_image_vision_agent_uses_mock_ai_message(configure_llm):
    configure_llm(mode="mock", scenario="defective_product")
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), "white").save(buffer, format="PNG")
    valid_image = buffer.getvalue()

    result = image_service._run_vision_assessment(
        valid_image,
        [valid_image],
        "Bluetooth Speaker",
        "electronics",
        "Portable speaker",
        "defective",
        [],
    )

    assert result["plausible"] is True
    assert result["image_quality"] == "good"


def test_malformed_image_replay_is_rejected(configure_llm):
    configure_llm(mode="mock", scenario="malformed_response")
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), "white").save(buffer, format="PNG")
    valid_image = buffer.getvalue()

    with pytest.raises(ValidationError):
        image_service._run_vision_assessment(
            valid_image,
            [valid_image],
            "Bluetooth Speaker",
            "electronics",
            "Portable speaker",
            "defective",
            [],
        )


def test_actual_decision_agent_falls_back_to_escalation_on_mock_failure(
    configure_llm,
    stub_external_services,
):
    configure_llm(mode="mock", scenario="decision_failure")
    case = make_case("low_risk")
    case.agent_results["gate"] = base.AgentResult(
        agent="gate",
        output=base.GateResult(ok=True, reason="ok"),
        confidence=None,
        model=None,
        started_at="2026-11-01T10:00:00+00:00",
        duration_ms=0,
        error=None,
    )

    proposal = asyncio.run(agents.decision(case))

    assert proposal.proposal == "escalate"
    assert "decision_llm_failure" in proposal.triggered_rules
    assert case.agent_results["decision"].error is None


def test_mock_mode_still_calls_actual_agents(configure_llm, monkeypatch):
    configure_llm(mode="mock", scenario="low_risk")
    original = agents.data_quality_gate
    called = False

    async def observed_gate(case):
        nonlocal called
        called = True
        return await original(case)

    monkeypatch.setattr(agents, "data_quality_gate", observed_gate)
    case = make_case("low_risk")

    asyncio.run(agents.data_quality_gate(case))

    assert called is True
