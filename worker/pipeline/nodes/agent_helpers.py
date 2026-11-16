from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from functools import lru_cache, wraps
from time import perf_counter
from typing import Any, Literal, TypeVar

from catboost import CatBoostClassifier

from ml.model_service import load_model
from worker.pipeline.nodes import base
from worker.pipeline.tracing import observation, update_observation

OutputT = TypeVar("OutputT", bound=base.AgentOutput)

RISK_WEIGHTS = {
    "legitimate": 0,
    "policy_abuser": 70,
    "fraudulent_return": 100,
    "wardrobing": 40,
}


def _record_result(
    agent_name: str,
    *,
    model: str | None = None,
    prompt_version: str | None = None,
) -> Callable[
    [Callable[[base.Case], Coroutine[Any, Any, OutputT]]],
    Callable[[base.Case], Coroutine[Any, Any, OutputT]],
]:
    def decorate(
        agent: Callable[[base.Case], Coroutine[Any, Any, OutputT]],
    ) -> Callable[[base.Case], Coroutine[Any, Any, OutputT]]:
        @wraps(agent)
        async def run(case: base.Case) -> OutputT:
            started_at = datetime.now(UTC).isoformat()
            started = perf_counter()
            trace_metadata = {
                "agent": agent_name,
                "model": model or "unspecified",
                "prompt_version": prompt_version or "unspecified",
            }
            trace_input = case.model_dump(mode="json")
            with observation(
                name=f"return-agent-{agent_name}",
                metadata=trace_metadata,
            ) as span:
                try:
                    output = await agent(case)
                except Exception as error:
                    duration_ms = round((perf_counter() - started) * 1000)
                    update_observation(
                        span,
                        status="error",
                        details={"duration_ms": duration_ms},
                        error_type=type(error).__name__,
                        input_data=trace_input,
                        output_data={
                            "error": f"{type(error).__name__}: {error}"
                        },
                    )
                    case.agent_results[agent_name] = base.AgentResult(
                        agent=agent_name,
                        output=None,
                        confidence=None,
                        started_at=started_at,
                        duration_ms=duration_ms,
                        error=f"{type(error).__name__}: {error}",
                        model=model,
                        prompt_version=prompt_version,
                    )
                    raise

                duration_ms = round((perf_counter() - started) * 1000)
                update_observation(
                    span,
                    status="success",
                    details={
                        "duration_ms": duration_ms,
                        "result_type": type(output).__name__,
                    },
                    input_data=trace_input,
                    output_data=output.model_dump(mode="json"),
                )
                case.agent_results[agent_name] = base.AgentResult(
                    agent=agent_name,
                    output=output,
                    confidence=None,
                    started_at=started_at,
                    duration_ms=duration_ms,
                    error=None,
                    model=model,
                    prompt_version=prompt_version,
                )
                if agent_name == "gate" and isinstance(output, base.GateResult):
                    case.gate_result = output
                return output

        return run

    return decorate


def _parse_llm_output[OutputT: base.AgentOutput](
    response: Any, schema: type[OutputT]
) -> OutputT:
    content = response.content
    if not isinstance(content, str):
        raise TypeError("Agent returned non-text content; expected a JSON object.")
    return schema.model_validate_json(content)


@lru_cache(maxsize=1)
def _behavior_model() -> CatBoostClassifier:
    """Load and cache the behavior-risk CatBoost model for this process."""
    return load_model()


def _recorded_output[OutputT: base.AgentOutput](
    case: base.Case,
    agent_name: str,
    output_type: type[OutputT],
) -> OutputT | None:
    result = case.agent_results.get(agent_name)
    if result is None or result.error is not None:
        return None
    if isinstance(result.output, output_type):
        return result.output
    return None


def _has_positive_signal(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "linked"}
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return False


def _build_decision_input(case: base.Case) -> base.DecisionInput:
    intake_result = _recorded_output(case, "intake", base.IntakeResult)
    policy_result = _recorded_output(case, "policy", base.PolicyResult)
    image_result = _recorded_output(case, "image", base.ImageResult)
    behavior_result = _recorded_output(case, "behavior", base.BehaviorResult)
    gate_result = _recorded_output(case, "gate", base.GateResult) or case.gate_result
    planner_result = _recorded_output(case, "planner", base.PlannerResult)
    features = behavior_result.features if behavior_result else {}

    linked_accounts_value = features.get("linked_accounts")
    linked_accounts = (
        int(linked_accounts_value)
        if isinstance(linked_accounts_value, (int, float))
        and not isinstance(linked_accounts_value, bool)
        else None
    )
    ring_linked = any(
        _has_positive_signal(features.get(key))
        for key in (
            "linked_accounts",
            "linked_with_denials",
            "multiple_accounts_flag",
            "refund_to_different_account",
            "ring_linked",
        )
    )
    ring_linked = ring_linked or _has_positive_signal(features.get("shared"))

    history_requires_behavior = (
        case.customer_history.returns >= base.MIN_PRIOR_RETURNS
        or case.customer_history.denied > 0
    )
    behavior_skipped_for_new_customer = (
        planner_result is not None
        and "behavior" in planner_result.skip
        and not history_requires_behavior
    )
    behavior_verification_required = (
        not behavior_skipped_for_new_customer or ring_linked
    )

    product = case.product_info
    order = case.order_info
    return base.DecisionInput(
        gate_result=gate_result,
        planner_result=planner_result,
        intake_result=intake_result,
        policy_result=policy_result,
        image_result=image_result,
        behavior_result=behavior_result,
        case_facts=base.DecisionCaseFacts(
            case_id=case.case_id,
            item_name=case.item_name,
            reason_code=case.reason_code,
            description=case.description,
            product_title=product.title if product else None,
            product_category=product.category if product else None,
            return_amount=order.return_amount if order else None,
            photos_present=bool(case.photos),
            image_verification_required=bool(case.photos),
            behavior_verification_required=behavior_verification_required,
            prior_returns=case.customer_history.returns,
            prior_denials=case.customer_history.denied,
            ring_linked=ring_linked,
            linked_accounts=linked_accounts,
        ),
    )


def _decision_evidence(decision_input: base.DecisionInput) -> list[str]:
    evidence: list[str] = []
    facts = decision_input.case_facts
    evidence.append(f"case_facts: reason_code={facts.reason_code}")
    if facts.return_amount is not None:
        evidence.append(f"case_facts: return_amount={facts.return_amount:.2f}")

    if decision_input.intake_result:
        intake_result = decision_input.intake_result
        evidence.append(
            "intake_result: "
            f"status={intake_result.status}; "
            f"missing_fields={intake_result.missing_fields}; "
            f"notes={intake_result.notes}"
        )
    if decision_input.policy_result:
        policy_result = decision_input.policy_result
        references = [
            f"{reference.document_id}@{reference.policy_version}:"
            f"{reference.section}/{reference.subsection or ''}"
            f"#{reference.chunk_index}"
            for reference in policy_result.policy_references
        ]
        evidence.append(
            "policy_result: "
            f"eligible={policy_result.eligible}; reason={policy_result.reason}; "
            f"references={references}"
        )
    if decision_input.image_result:
        image_result = decision_input.image_result
        evidence.append(
            "image_result: "
            f"match={image_result.match}; "
            f"similarity={image_result.similarilty:.4f}; "
            f"fake_detected={image_result.fake_probabilty}"
        )
        for vision in image_result.vision_call:
            evidence.append(
                "image_result.vision_call: "
                f"plausible={vision.plausible}; "
                f"image_quality={vision.image_quality}; note={vision.note}"
            )
    if decision_input.behavior_result:
        behavior_result = decision_input.behavior_result
        evidence.append(
            "behavior_result: "
            f"risk_score={behavior_result.risk_score:.4f}; "
            f"predicted_class={behavior_result.predicted_class}"
        )
    elif (
        decision_input.planner_result is not None
        and not decision_input.case_facts.behavior_verification_required
    ):
        evidence.append(
            "planner_result: behavior skipped for a customer with no prior "
            "returns or denials; decision risk_score=0.0 (not a model score)"
        )
    return evidence


def _decision_risk_score(decision_input: base.DecisionInput) -> float:
    if decision_input.behavior_result is not None:
        return decision_input.behavior_result.risk_score
    if decision_input.case_facts.behavior_verification_required:
        return 1.0
    return 0.0


def _validate_decision_proposal(
    decision_input: base.DecisionInput,
    llm_proposal: base.DecisionProposal,
) -> base.DecisionProposal:
    facts = decision_input.case_facts
    behavior_result = decision_input.behavior_result
    policy_result = decision_input.policy_result
    intake_result = decision_input.intake_result
    image_result = decision_input.image_result
    risk_score = _decision_risk_score(decision_input)
    evidence = _decision_evidence(decision_input)
    escalation_rules: list[str] = []
    if "decision_llm_failure" in llm_proposal.triggered_rules:
        escalation_rules.append("decision_llm_failure")

    if decision_input.gate_result is not None and not decision_input.gate_result.ok:
        escalation_rules.append("data_quality_gate_failed")
    if intake_result is None:
        escalation_rules.append("missing_intake_result")
    elif intake_result.status != "match" or intake_result.missing_fields:
        escalation_rules.append("intake_incomplete_or_mismatched")

    if policy_result is None:
        escalation_rules.append("missing_policy_result")
    elif policy_result.eligible == "unclear":
        escalation_rules.append("policy_eligibility_unclear")

    image_required = (
        facts.image_verification_required
        or (
            decision_input.planner_result is not None
            and "image" in decision_input.planner_result.next_steps
        )
    )
    if image_required and image_result is None:
        escalation_rules.append("missing_required_image_result")
    if image_result is not None:
        if not image_result.match:
            escalation_rules.append("image_product_mismatch")
        if image_result.fake_probabilty:
            escalation_rules.append("suspicious_image_authenticity")
        if any(
            vision.plausible is not True or vision.image_quality == "poor"
            for vision in image_result.vision_call
        ):
            escalation_rules.append("uncertain_or_mismatched_vision_assessment")

    if behavior_result is None and facts.behavior_verification_required:
        escalation_rules.append("missing_behavior_result")
    elif behavior_result is not None and behavior_result.risk_score > 0.15:
        escalation_rules.append("behavioral_risk_above_approval_threshold")

    if facts.ring_linked:
        escalation_rules.append("linked_or_suspicious_accounts")
    if (
        facts.return_amount is not None
        and facts.return_amount > facts.high_value_threshold
    ):
        escalation_rules.append("high_value_refund")

    explicit_policy_violation = bool(
        policy_result is not None
        and policy_result.eligible is False
        and policy_result.reason.strip()
        and policy_result.policy_references
    )
    if (
        policy_result is not None
        and policy_result.eligible is False
        and not explicit_policy_violation
    ):
        escalation_rules.append("policy_denial_lacks_cited_support")

    if (
        intake_result is not None
        and intake_result.status == "mismatch"
        and policy_result is not None
        and policy_result.eligible is True
    ):
        escalation_rules.append("intake_policy_contradiction")

    if llm_proposal.confidence < 0.80:
        escalation_rules.append("decision_confidence_below_approval_threshold")

    if escalation_rules:
        final_proposal: Literal["approve", "deny", "escalate"] = "escalate"
        triggered_rules = list(dict.fromkeys(escalation_rules))
        review_required = True
        rationale = "Deterministic safeguards require human review."
    elif explicit_policy_violation:
        final_proposal = "deny"
        triggered_rules = ["cited_policy_ineligibility"]
        review_required = False
        rationale = "The policy result explicitly found ineligibility and cited supporting policy references."
    elif llm_proposal.proposal == "approve":
        final_proposal = "approve"
        triggered_rules = ["all_required_checks_passed"]
        review_required = False
        rationale = "Mandatory approval checks passed."
    else:
        final_proposal = "escalate"
        triggered_rules = ["decision_requires_human_review"]
        if llm_proposal.proposal == "deny":
            triggered_rules.append("unsupported_denial_proposal")
            rationale = "The proposed denial is not supported by a cited policy violation."
        else:
            rationale = "The Decision Agent recommends human review."
        review_required = True

    return base.DecisionProposal(
        proposal=final_proposal,
        confidence=llm_proposal.confidence,
        reasoning=f"{llm_proposal.reasoning} {rationale}".strip(),
        risk_score=risk_score,
        triggered_rules=triggered_rules,
        evidence=evidence,
        requires_human_review=review_required,
    )


def _decision_failure_fallback(
    decision_input: base.DecisionInput,
) -> base.DecisionProposal:
    return base.DecisionProposal(
        proposal="escalate",
        confidence=0.0,
        reasoning=(
            "Decision reasoning was unavailable or invalid; deterministic "
            "fallback requires human review."
        ),
        risk_score=_decision_risk_score(decision_input),
        triggered_rules=["decision_llm_failure"],
        evidence=_decision_evidence(decision_input),
        requires_human_review=True,
    )


def _build_explanation_input(case: base.Case) -> base.ExplanationInput:
    decision_result = case.agent_results.get("decision")
    if (
        decision_result is None
        or decision_result.error is not None
        or not isinstance(decision_result.output, base.DecisionProposal)
    ):
        raise ValueError(
            "Explanation Agent requires a successful Decision Agent proposal."
        )

    decision_output = decision_result.output
    product_name = (
        case.product_info.title
        if case.product_info is not None
        else case.item_name
    )
    key_reasons: list[str] = []
    intake_result = _recorded_output(case, "intake", base.IntakeResult)
    policy_result = _recorded_output(case, "policy", base.PolicyResult)
    image_result = _recorded_output(case, "image", base.ImageResult)

    if decision_output.proposal == "approve":
        if policy_result is not None and policy_result.eligible is True:
            key_reasons.append("The request meets the return policy requirements.")
        if intake_result is not None and intake_result.status == "match":
            key_reasons.append(
                "The return details are consistent with the item and reason provided."
            )
        if image_result is not None and image_result.match:
            key_reasons.append("The submitted photo is consistent with the item.")
    elif decision_output.proposal == "deny":
        if policy_result is not None and policy_result.eligible is False:
            key_reasons.append(f"Policy reason: {policy_result.reason.strip()}")
    else:
        key_reasons.append(
            "More information or review is needed before we can confirm the outcome."
        )
        if image_result is not None and (
            not image_result.match or image_result.fake_probabilty
        ):
            key_reasons.append(
                "The submitted photo needs a closer review to verify the item."
            )
        if intake_result is not None and intake_result.status != "match":
            key_reasons.append(
                "Some return details need clarification or further review."
            )

    if not key_reasons:
        key_reasons.append(
            "The request was assessed using the information provided."
        )

    return base.ExplanationInput(
        proposal=decision_output.proposal,
        requires_human_review=decision_output.requires_human_review,
        product_name=product_name,
        reason_code=case.reason_code,
        key_reasons=key_reasons,
    )


def _explanation_failure_fallback(
    explanation_input: base.ExplanationInput,
) -> base.ExplanationResult:
    product = explanation_input.product_name
    if explanation_input.proposal == "approve":
        message = (
            f"Your return request for {product} is recommended for approval. "
            "Any refund will be handled through the normal return process."
        )
    elif explanation_input.proposal == "deny":
        message = (
            f"Our current review recommends that the return request for "
            f"{product} not be approved because it does not meet the return "
            "policy requirements. This is a recommendation, not a completed "
            "return transaction."
        )
    else:
        message = (
            f"We need additional time to review your return request for "
            f"{product}. We’ll update you when the review is complete."
        )
    return base.ExplanationResult(message=message)
