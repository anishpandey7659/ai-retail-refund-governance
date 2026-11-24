from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable, RunnableConfig
from pydantic import BaseModel


class MockLLMFailure(RuntimeError):
    """A deliberate mock response requesting an LLM failure."""


class MissingMockResponseError(LookupError):
    """Raised when a mock or replay scenario has no response for an agent."""


DEFAULT_SCENARIO_RESPONSES: dict[str, dict[str, Any]] = {
    "low_risk": {
        "intake": {
            "status": "match",
            "missing_fields": [],
            "notes": "The return details match the purchased product.",
        },
        "policy": {
            "eligible": True,
            "reason": "The return is within the policy period.",
            "policy_references": [
                {
                    "document_id": "return-policy",
                    "policy_version": "v1",
                    "section": "Return eligibility",
                    "subsection": None,
                    "chunk_index": 0,
                }
            ],
        },
        "behavior": {
            "message": "The available account history is consistent with ordinary use."
        },
        "decision": {
            "proposal": "approve",
            "confidence": 0.98,
            "reasoning": "The required checks support approval.",
            "risk_score": 0.02,
            "triggered_rules": [],
            "evidence": [],
            "requires_human_review": False,
        },
        "explanation": {
            "message": (
                "Your return request is recommended for approval. Any refund will "
                "be handled through the normal return process."
            )
        },
        "image": {
            "plausible": True,
            "confidence": 0.95,
            "observed_product": "The pictured item matches the catalog product.",
            "matches": ["Product appearance"],
            "mismatches": [],
            "image_quality": "good",
            "note": "The images appear consistent.",
        },
    },
    "high_risk": {
        "intake": {
            "status": "match",
            "missing_fields": [],
            "notes": "The return details match the purchased product.",
        },
        "policy": {
            "eligible": True,
            "reason": "The return is within the policy period.",
            "policy_references": [
                {
                    "document_id": "return-policy",
                    "policy_version": "v1",
                    "section": "Return eligibility",
                    "subsection": None,
                    "chunk_index": 0,
                }
            ],
        },
        "behavior": {
            "message": "The account history warrants additional review."
        },
        "decision": {
            "proposal": "approve",
            "confidence": 0.96,
            "reasoning": "The required checks support approval.",
            "risk_score": 0.7,
            "triggered_rules": [],
            "evidence": [],
            "requires_human_review": False,
        },
        "explanation": {
            "message": (
                "We need additional time to review your return request. We will "
                "update you when the review is complete."
            )
        },
        "image": {
            "plausible": True,
            "confidence": 0.95,
            "observed_product": "The pictured item matches the catalog product.",
            "matches": ["Product appearance"],
            "mismatches": [],
            "image_quality": "good",
            "note": "The images appear consistent.",
        },
    },
    "suspicious": {
        "intake": {
            "status": "match",
            "missing_fields": [],
            "notes": "The return details match the purchased product.",
        },
        "policy": {
            "eligible": True,
            "reason": "The return is within the policy period.",
            "policy_references": [
                {
                    "document_id": "return-policy",
                    "policy_version": "v1",
                    "section": "Return eligibility",
                    "subsection": None,
                    "chunk_index": 0,
                }
            ],
        },
        "behavior": {
            "message": "The available account history is consistent with ordinary use."
        },
        "decision": {
            "proposal": "approve",
            "confidence": 0.96,
            "reasoning": "The required checks support approval.",
            "risk_score": 0.02,
            "triggered_rules": [],
            "evidence": [],
            "requires_human_review": False,
        },
        "explanation": {
            "message": (
                "We need additional time to review your return request. We will "
                "update you when the review is complete."
            )
        },
        "image": {
            "plausible": False,
            "confidence": 0.35,
            "observed_product": "The pictured item is not clearly identifiable.",
            "matches": [],
            "mismatches": ["Product identity is uncertain"],
            "image_quality": "poor",
            "note": "The image requires human review.",
        },
    },
    "defective_product": {
        "intake": {
            "status": "match",
            "missing_fields": [],
            "notes": "The return details match the purchased product.",
        },
        "policy": {
            "eligible": True,
            "reason": "Defective products are eligible within the policy period.",
            "policy_references": [
                {
                    "document_id": "return-policy",
                    "policy_version": "v1",
                    "section": "Defective products",
                    "subsection": None,
                    "chunk_index": 1,
                }
            ],
        },
        "behavior": {
            "message": "The available account history is consistent with ordinary use."
        },
        "decision": {
            "proposal": "approve",
            "confidence": 0.98,
            "reasoning": "The required checks support approval.",
            "risk_score": 0.02,
            "triggered_rules": [],
            "evidence": [],
            "requires_human_review": False,
        },
        "explanation": {
            "message": (
                "Your return request for the defective product is recommended for "
                "approval. Any refund will be handled through the normal process."
            )
        },
        "image": {
            "plausible": True,
            "confidence": 0.95,
            "observed_product": "The pictured item matches the catalog product.",
            "matches": ["Product appearance"],
            "mismatches": [],
            "image_quality": "good",
            "note": "The images appear consistent.",
        },
    },
}

DEFAULT_SCENARIO_RESPONSES["llm_failure"] = {
    **DEFAULT_SCENARIO_RESPONSES["low_risk"],
    "intake": {"$error": "Simulated intake LLM failure."},
}
DEFAULT_SCENARIO_RESPONSES["malformed_response"] = {
    **DEFAULT_SCENARIO_RESPONSES["low_risk"],
    "intake": {
        "status": "not-a-valid-intake-status",
        "missing_fields": [],
        "notes": "This response is intentionally invalid.",
    },
    "image": "not valid JSON",
}
DEFAULT_SCENARIO_RESPONSES["decision_failure"] = {
    **DEFAULT_SCENARIO_RESPONSES["low_risk"],
    "decision": {"$error": "Simulated decision LLM failure."},
}

_UNSET = object()


class MockLLM(Runnable[LanguageModelInput, Any]):
    """Deterministic LangChain Runnable for mock and replay LLM execution."""

    def __init__(
        self,
        agent: str,
        *,
        scenario: str,
        schema: type[BaseModel] | None = None,
        agent_responses: Mapping[str, Any] | None = None,
        scenario_responses: Mapping[str, Mapping[str, Any]] | None = None,
        replay_file: str | Path | None = None,
    ) -> None:
        self.agent = agent
        self.scenario = scenario
        self.schema = schema
        self.agent_responses = agent_responses or {}
        self.scenario_responses = scenario_responses or {}
        self.replay_file = Path(replay_file).expanduser() if replay_file else None
        self._replay_data = self._read_replay_file() if self.replay_file else None

    def with_structured_output(self, schema: type[BaseModel], **_: Any) -> MockLLM:
        return MockLLM(
            self.agent,
            scenario=self.scenario,
            schema=schema,
            agent_responses=self.agent_responses,
            scenario_responses=self.scenario_responses,
            replay_file=self.replay_file,
        )

    def invoke(
        self,
        input: LanguageModelInput,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> Any:
        del input, config, kwargs
        response = self._select_response()
        if isinstance(response, BaseException):
            raise response
        if isinstance(response, Mapping) and "$error" in response:
            raise MockLLMFailure(str(response["$error"]))

        if self.schema is not None:
            return self._validate_structured_response(response)
        return self._as_ai_message(response)

    def _read_replay_file(self) -> Mapping[str, Any]:
        assert self.replay_file is not None
        payload = json.loads(self.replay_file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(
            payload.get("scenarios"), dict
        ):
            raise TypeError(
                "LLM replay file must contain an object with a 'scenarios' mapping."
            )
        return payload["scenarios"]

    def _select_response(self) -> Any:
        if self._replay_data is not None:
            scenario_responses = self._replay_data.get(self.scenario)
            if not isinstance(scenario_responses, dict):
                raise MissingMockResponseError(
                    f"Replay scenario {self.scenario!r} is missing."
                )
            response = scenario_responses.get(self.agent, _UNSET)
            if response is _UNSET:
                raise MissingMockResponseError(
                    f"Replay response for agent {self.agent!r} is missing from "
                    f"scenario {self.scenario!r}."
                )
            return response

        scenario_responses = self.scenario_responses.get(self.scenario, {})
        response = scenario_responses.get(self.agent, _UNSET)
        if response is _UNSET:
            response = self.agent_responses.get(self.agent, _UNSET)
        if response is _UNSET:
            raise MissingMockResponseError(
                f"No mock response configured for agent {self.agent!r} in "
                f"scenario {self.scenario!r}."
            )
        return response

    def _validate_structured_response(self, response: Any) -> BaseModel:
        assert self.schema is not None
        if isinstance(response, self.schema):
            return response
        if isinstance(response, BaseModel):
            response = response.model_dump(mode="python")
        if isinstance(response, str):
            return self.schema.model_validate_json(response)
        return self.schema.model_validate(response)

    @staticmethod
    def _as_ai_message(response: Any) -> AIMessage:
        if isinstance(response, AIMessage):
            return response
        if isinstance(response, BaseModel):
            response = response.model_dump(mode="json")
        if isinstance(response, str):
            content = response
        elif isinstance(response, Mapping):
            content = json.dumps(response)
        else:
            raise TypeError(
                "Mock image-model responses must be strings, mappings, "
                "Pydantic models, or AIMessage objects."
            )
        return AIMessage(content=content)
