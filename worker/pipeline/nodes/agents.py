import asyncio
import json

import pandas as pd

from ml.image_service import analyze_image
from ml.model_service import risk_probability
from worker.pipeline.config import get_settings
from worker.pipeline.llm import init_chat
from worker.pipeline.logger import get_logger
from worker.pipeline.nodes import base
from worker.pipeline.nodes.agent_helpers import (
    RISK_WEIGHTS,
    _behavior_model,
    _build_decision_input,
    _build_explanation_input,
    _decision_failure_fallback,
    _explanation_failure_fallback,
    _parse_llm_output,
    _record_result,
    _validate_decision_proposal,
)

logger = get_logger(__name__)

_settings = get_settings()
DECISION_MODEL = (
    f"{_settings.llm_provider}/{_settings.llm_model}; "
    f"fallback={_settings.fallback_llm_provider}/{_settings.fallback_llm_model}"
)


@_record_result("gate")
async def data_quality_gate(case: base.Case) -> base.GateResult:
    """Check that a return case has the minimum information for review."""
    if not case.item_name:
        return base.GateResult(ok=False, reason="missing item name")
    if case.reason_code in base.PHOTO_REQUIRED and not case.photos:
        return base.GateResult(
            ok=False, reason="photo required for this return reason"
        )
    if not case.product_info:
        return base.GateResult(
            ok=False, reason="no product info to compare against"
        )
    return base.GateResult(ok=True, reason="All required fields present")


@_record_result("planner")
async def planner(case: base.Case) -> base.PlannerResult:
    """Select pipeline steps based on photos and customer return history."""
    steps: list[base.AgentStep] = ["intake", "policy"]
    skipped: list[base.SkippedAgentStep] = []
    reasons = []

    if case.photos:
        steps.append("image")
        reasons.append("photo attached, run image check")
    else:
        skipped.append("image")
        reasons.append("no photo, skip image")

    history = case.customer_history
    if history.returns >= base.MIN_PRIOR_RETURNS or history.denied > 0:
        steps.append("behavior")
        reasons.append(
            f"{history.returns} prior returns "
            f"({history.denied} denied, rate {history.return_rate:.0%}), "
            "run behavior check"
        )
    else:
        skipped.append("behavior")
        reasons.append("no prior returns, skip behavior")

    steps.extend(["decision", "critic", "explanation"])
    return base.PlannerResult(
        next_steps=steps,
        skip=skipped,
        reason="; ".join(reasons),
    )


@_record_result("intake")
async def intake(case: base.Case) -> base.IntakeResult:
    """Ask the language model to assess the return case's intake information."""
    from worker.pipeline.prompts.intake import PROMPT, intake_vars

    prompt = PROMPT.format(**intake_vars(case))
    result = init_chat().invoke(prompt)
    return _parse_llm_output(result, base.IntakeResult)


@_record_result("policy")
async def policy(case: base.Case) -> base.PolicyResult:
    """Assess return eligibility using retrieved policy context."""
    from worker.pipeline.dependency import get_policy_knowledge_base
    from worker.pipeline.prompts.policy import (
        PROMPT,
        build_queries,
        policy_vars,
    )

    retrieval_threshold = 0.50
    retrieved_chunks = await get_policy_knowledge_base().search_policy(
        build_queries(case)
    )
    filtered_chunks = [
        chunk
        for chunk in retrieved_chunks
        if chunk.get("score", 0) >= retrieval_threshold
    ]
    policy_context = "\n\n".join(
        (
            f"[DOCUMENT_ID: {chunk['document_id']}]\n"
            f"[POLICY_VERSION: {chunk['policy_version']}]\n"
            f"[SECTION: {chunk['section']}]\n"
            f"[SUBSECTION: {chunk.get('subsection', 'N/A')}]\n"
            f"[CHUNK_INDEX: {chunk['chunk_index']}]\n"
            f"[CONTENT]\n{chunk['content']}"
        )
        for chunk in filtered_chunks
    )
    inputs = policy_vars(case)
    inputs["retrive_chunks"] = policy_context
    response = init_chat().invoke(PROMPT.invoke(inputs))
    return _parse_llm_output(response, base.PolicyResult)


@_record_result("image")
async def image(case: base.Case) -> base.ImageResult:
    """Assess return photos for product match and image authenticity."""
    if not case.photos:
        raise ValueError(f"Return {case.case_id} has no return photos to inspect.")
    if case.product_info is None or not case.product_info.image_key:
        raise ValueError(
            f"Return {case.case_id} has no catalog image to compare against."
        )

    result = await asyncio.to_thread(
        analyze_image,
        [photo.object_key for photo in case.photos],
        case.product_info.image_key,
        case.product_info.title,
        case.product_info.category,
        case.product_info.description,
        case.reason_code,
    )
    return base.ImageResult.model_validate(result)


@_record_result("behavior")
async def behavior(case: base.Case) -> base.BehaviorResult:
    """Calculate behavior risk and generate a plain-English explanation."""
    from worker.pipeline.helper import load_ml_context
    from worker.pipeline.prompts.behavior import PROMPT

    context = await load_ml_context(case.case_id)
    model = _behavior_model()
    if model.feature_names_ is None:
        raise ValueError("The behavior model does not expose its feature names.")

    feature_names = list(model.feature_names_)
    missing_features = [name for name in feature_names if name not in context]
    if missing_features:
        raise ValueError(f"ML context is missing model features: {missing_features}")

    unavailable_features = [name for name in feature_names if context[name] is None]
    if unavailable_features:
        raise ValueError(
            f"Cannot score return {case.case_id}; these features are unavailable: "
            f"{unavailable_features}"
        )

    features = pd.DataFrame(
        [{name: context[name] for name in feature_names}],
        columns=feature_names,
    )
    predictions = risk_probability(model=model, X=features)
    if len(predictions) != 1:
        raise RuntimeError(
            f"Expected one prediction for return {case.case_id}, got {len(predictions)}"
        )

    prediction = predictions[0]
    probabilities = prediction["class_probabilities"]
    missing_classes = [name for name in RISK_WEIGHTS if name not in probabilities]
    if missing_classes:
        raise ValueError(
            f"Model probabilities are missing risk classes: {missing_classes}"
        )

    risk_score = sum(
        probabilities[class_name] * weight
        for class_name, weight in RISK_WEIGHTS.items()
    ) / 100
    if not 0 <= risk_score <= 1:
        raise ValueError(f"Calculated risk score is out of range: {risk_score}")

    response = init_chat().invoke(
        PROMPT.format(
            risk_score=f"{risk_score:.4f}",
            predicted_class=prediction["predicted_class"],
            probabilities_json=json.dumps(probabilities, sort_keys=True),
            features_json=json.dumps(context, sort_keys=True, default=str),
        )
    )
    summary = response.content
    if not isinstance(summary, str) or not summary.strip():
        raise TypeError("Behavior explanation LLM returned no plain-text summary.")

    return base.BehaviorResult(
        risk_score=risk_score,
        predicted_class=prediction["predicted_class"],
        class_probabilities=probabilities,
        summary=summary.strip(),
        features=context,
    )


@_record_result(
    "decision",
    model=DECISION_MODEL,
    prompt_version="decision-v1",
)
async def decision(case: base.Case) -> base.DecisionProposal:
    """Propose a return decision and enforce mandatory rules deterministically."""
    from worker.pipeline.prompts.decision import PROMPT

    decision_input = _build_decision_input(case)
    prompt = PROMPT.format(
        decision_input=decision_input.model_dump_json(indent=2)
    )
    try:
        response = await asyncio.to_thread(init_chat().invoke, prompt)
        llm_proposal = _parse_llm_output(response, base.DecisionProposal)
    except Exception:
        logger.exception(
            "Decision Agent failed; returning a human-review fallback",
            extra={"case_id": case.case_id},
        )
        return _validate_decision_proposal(
            decision_input,
            _decision_failure_fallback(decision_input),
        )

    return _validate_decision_proposal(decision_input, llm_proposal)


@_record_result(
    "explanation",
    model=DECISION_MODEL,
    prompt_version="explanation-v1",
)
async def explanation(case: base.Case) -> base.ExplanationResult:
    """Write one customer-safe paragraph for the recorded decision proposal."""
    from worker.pipeline.prompts.explanation import PROMPT

    explanation_input = _build_explanation_input(case)
    prompt = PROMPT.format(
        explanation_input=explanation_input.model_dump_json(indent=2)
    )
    try:
        response = await asyncio.to_thread(init_chat().invoke, prompt)
        result = _parse_llm_output(response, base.ExplanationResult)
        message = " ".join(result.message.split())
        restricted_phrases = (
            "risk score",
            "risk level",
            "fraud",
            "suspicious",
            "linked account",
            "behavioral risk",
            "triggered rule",
            "decision agent",
            "confidence score",
            "model prediction",
            "refund has been issued",
            "refund was issued",
            "refund has been processed",
            "refund was processed",
        )
        if any(phrase in message.lower() for phrase in restricted_phrases):
            raise ValueError(
                "Explanation contains internal signals or unsupported processing claims."
            )
        return base.ExplanationResult(message=message)
    except Exception:
        logger.exception(
            "Explanation Agent failed; returning a safe template",
            extra={"case_id": case.case_id},
        )
        return _explanation_failure_fallback(explanation_input)
