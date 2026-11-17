from typing import TypedDict, cast

from langgraph.graph import END, START, StateGraph

from worker.pipeline.logger import get_logger
from worker.pipeline.nodes import agents, base
from worker.pipeline.tracing import observation, update_observation

logger = get_logger(__name__)

PRE_DECISION_AGENTS = frozenset({"intake", "policy", "image", "behavior"})


class WorkflowState(TypedDict):
    case: base.Case
    gate_result: base.GateResult
    planner_steps: list[str]
    agent_index: int
    skip_workflow: bool
    skip_reason: str | None


async def run_workflow(case: base.Case) -> WorkflowState:
    """Run the return-review workflow and return its complete final state.

    The workflow runs the data-quality gate first and stops immediately if it
    fails. Otherwise, it executes planner-selected evidence agents, then records
    a decision proposal and customer-safe explanation. Agent failures are
    retained on the case and do not prevent a safe decision. Intake and policy
    outcomes and the decision proposal update the case status; no refund is
    executed here.
    """
    with observation(
        name="return-review-workflow",
        metadata={"workflow": "return-review"},
    ) as span:
        try:
            result = await _run_workflow(case)
        except Exception as error:
            logger.exception(
                "Return review workflow failed",
                extra={
                    "case_id": case.case_id,
                    "error_type": type(error).__name__,
                },
            )
            update_observation(
                span,
                status="error",
                error_type=type(error).__name__,
            )
            raise
        update_observation(span, status="success")
    logger.info(
        "Return review workflow completed",
        extra={
            "case_id": result["case"].case_id,
            "final_status": result["case"].status,
        },
    )
    return result


async def _run_data_quality_gate(state: WorkflowState) -> dict:
    result = await agents.data_quality_gate(state["case"])
    if not result.ok:
        state["case"].status = "in_review"
    return {
        "gate_result": result,
        "skip_workflow": not result.ok,
        "skip_reason": result.reason if not result.ok else None,
    }


async def _run_planner(state: WorkflowState) -> dict:
    result = await agents.planner(state["case"])
    return {
        "planner_steps": [
            step for step in result.next_steps if step in PRE_DECISION_AGENTS
        ],
        "agent_index": 0,
    }


def _route_after_planner(state: WorkflowState) -> str:
    return _route_selected_agent(state)


def _route_after_gate(state: WorkflowState) -> str:
    if state["gate_result"].ok:
        return "planner"
    case = state["case"]
    logger.info(
        "Data-quality gate failed; skipping workflow",
        extra={
            "case_id": case.case_id,
            "reason_code": state["gate_result"].reason,
        },
    )
    return "end"

def _route_selected_agent(state: WorkflowState) -> str:
    if state.get("skip_workflow"):
        case = state["case"]
        logger.info(
            "Agent result requires workflow skip",
            extra={
                "case_id": case.case_id,
                "agent": (
                    state["planner_steps"][state["agent_index"] - 1]
                    if state["agent_index"] > 0
                    else "unknown"
                ),
                "status": case.status,
            },
        )
        return "end"
    if state["agent_index"] < len(state["planner_steps"]):
        return "selected_agent"
    return "decision"


async def _run_selected_agent(state: WorkflowState) -> dict:
    case = state["case"]
    agent_name = state["planner_steps"][state["agent_index"]]
    try:
        await getattr(agents, agent_name)(case)
    except Exception:
        logger.exception(
            "Workflow agent failed; continuing to a safe decision",
            extra={
                "case_id": case.case_id,
                "agent": agent_name,
            },
        )

    if agent_name == "intake":
        intake_result = case.agent_results.get("intake")
        output = intake_result.output if intake_result is not None else None
        if isinstance(output, base.IntakeResult) and output.status in {
            "mismatch",
            "missing_info",
        }:
            case.status = "denied"
            logger.info(
                "Intake stopped the workflow",
                extra={
                    "agent": agent_name,
                    "case_id": case.case_id,
                    "status": output.status,
                    "reason_code": output.status,
                },
            )
            return {
                "agent_index": state["agent_index"] + 1,
                "skip_workflow": True,
                "skip_reason": output.notes,
            }
    elif agent_name == "policy":
        policy_result = case.agent_results.get("policy")
        output = policy_result.output if policy_result is not None else None
        if isinstance(output, base.PolicyResult) and (
            output.eligible is False or output.eligible == "unclear"
        ):
            case.status = "denied" if output.eligible is False else "in_review"
            logger.info(
                "Policy stopped the workflow",
                extra={
                    "agent": agent_name,
                    "case_id": case.case_id,
                    "status": "ineligible" if output.eligible is False else "unclear",
                },
            )
            return {
                "agent_index": state["agent_index"] + 1,
                "skip_workflow": True,
                "skip_reason": output.reason,
            }

    return {
        "agent_index": state["agent_index"] + 1,
        "skip_workflow": False,
        "skip_reason": None,
    }

async def _run_decision(state: WorkflowState) -> dict:
    proposal = await agents.decision(state["case"])
    if proposal.proposal == "approve":
        state["case"].status = "approved"
    elif proposal.proposal == "deny":
        state["case"].status = "denied"
    else:
        state["case"].status = "escalated"
    logger.info(
        "Decision proposal recorded",
        extra={
            "case_id": state["case"].case_id,
            "proposal": proposal.proposal,
            "final_status": state["case"].status,
        },
    )
    return {}


async def _run_explanation(state: WorkflowState) -> dict:
    await agents.explanation(state["case"])
    return {}


def _build_workflow():
    builder = StateGraph(WorkflowState)
    builder.add_node("data_quality_gate", _run_data_quality_gate)
    builder.add_node("planner", _run_planner)
    builder.add_node("selected_agent", _run_selected_agent)
    builder.add_node("decision", _run_decision)
    builder.add_node("explanation", _run_explanation)

    builder.add_edge(START, "data_quality_gate")
    builder.add_conditional_edges(
        "data_quality_gate",
        _route_after_gate,
        {"planner": "planner", "end": END},
    )
    builder.add_conditional_edges(
        "planner",
        _route_after_planner,
        {
            "selected_agent": "selected_agent",
            "decision": "decision",
        },
    )
    builder.add_conditional_edges(
        "selected_agent",
        _route_selected_agent,
        {
            "selected_agent": "selected_agent",
            "decision": "decision",
            "end": END,
        },
    )
    builder.add_edge("decision", "explanation")
    builder.add_edge("explanation", END)
    return builder.compile()


_workflow = _build_workflow()


async def _run_workflow(case: base.Case) -> WorkflowState:
    state: WorkflowState = {
        "case": case,
        "gate_result": base.GateResult(ok=False, reason="Gate has not run."),
        "planner_steps": [],
        "agent_index": 0,
        "skip_workflow": False,
        "skip_reason": None,
    }
    result = await _workflow.ainvoke(state)
    return cast(WorkflowState, result)
