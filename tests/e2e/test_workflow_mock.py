import asyncio

import pytest

from tests.fixtures.return_cases import make_case
from worker.pipeline.workflow import run_workflow

EXPECTED_STATUSES = {
    "low_risk": "approved",
    "high_risk": "escalated",
    "suspicious": "escalated",
    "defective_product": "approved",
}


@pytest.mark.parametrize("mode", ["mock", "replay"])
@pytest.mark.parametrize("scenario,expected_status", EXPECTED_STATUSES.items())
def test_full_graph_runs_actual_agents_for_return_scenarios(
    mode,
    scenario,
    expected_status,
    configure_llm,
    stub_external_services,
    replay_file,
):
    configure_llm(
        mode=mode,
        scenario=scenario,
        replay_file=str(replay_file) if mode == "replay" else None,
    )
    case = make_case(scenario)

    result = asyncio.run(run_workflow(case))
    final_case = result["case"]

    assert final_case.status == expected_status
    assert {
        "gate",
        "planner",
        "intake",
        "policy",
        "behavior",
        "decision",
        "explanation",
    }.issubset(final_case.agent_results)
    assert all(
        final_case.agent_results[name].error is None
        for name in (
            "gate",
            "planner",
            "intake",
            "policy",
            "behavior",
            "decision",
            "explanation",
        )
    )
    if scenario in {"suspicious", "defective_product"}:
        assert final_case.agent_results["image"].error is None


@pytest.mark.parametrize("scenario", ["llm_failure", "malformed_response"])
def test_intake_llm_failures_are_recorded_and_escalated_safely(
    scenario,
    configure_llm,
    stub_external_services,
):
    configure_llm(mode="mock", scenario=scenario)
    case = make_case("low_risk")

    result = asyncio.run(run_workflow(case))

    assert result["case"].status == "escalated"
    assert result["case"].agent_results["intake"].error is not None
    assert result["case"].agent_results["decision"].error is None
    assert result["case"].agent_results["explanation"].error is None
