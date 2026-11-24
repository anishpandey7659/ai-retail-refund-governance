import json

import pytest

from worker.pipeline import dependency, helper
from worker.pipeline.config import get_settings
from worker.pipeline.llm import _live_chat, _live_image_model
from worker.pipeline.mock_llm import DEFAULT_SCENARIO_RESPONSES
from worker.pipeline.nodes import agents
from worker.pipeline.tracing import get_langfuse_client

BEHAVIOR_FEATURES = [
    "return_rate_pct",
    "customer_support_contacts",
    "refund_to_order_ratio",
    "previous_dispute_count",
    "item_returned_opened",
    "multiple_accounts_flag",
    "refund_to_different_account",
    "refund_amount_requested_usd",
    "return_reason",
    "address_change_before_delivery",
]


@pytest.fixture(autouse=True)
def isolate_cached_settings(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "")
    get_settings.cache_clear()
    get_langfuse_client.cache_clear()
    yield
    get_settings.cache_clear()
    get_langfuse_client.cache_clear()
    _live_chat.cache_clear()
    _live_image_model.cache_clear()


@pytest.fixture
def configure_llm(monkeypatch):
    def configure(
        *,
        mode: str = "mock",
        scenario: str = "low_risk",
        replay_file: str | None = None,
    ) -> None:
        monkeypatch.setenv("LLM_MODE", mode)
        monkeypatch.setenv("LLM_SCENARIO", scenario)
        if replay_file is None:
            monkeypatch.delenv("LLM_REPLAY_FILE", raising=False)
        else:
            monkeypatch.setenv("LLM_REPLAY_FILE", replay_file)
        get_settings.cache_clear()
        get_langfuse_client.cache_clear()

    return configure


@pytest.fixture
def replay_file(tmp_path):
    path = tmp_path / "llm-replay.json"
    path.write_text(
        json.dumps({"scenarios": DEFAULT_SCENARIO_RESPONSES}),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def stub_external_services(monkeypatch):
    class PolicyKnowledgeBaseStub:
        async def search_policy(self, queries):
            assert queries
            return [
                {
                    "score": 0.9,
                    "document_id": "return-policy",
                    "policy_version": "v1",
                    "section": "Return eligibility",
                    "subsection": None,
                    "chunk_index": 0,
                    "content": "Eligible returns must meet the return policy.",
                }
            ]

    class BehaviorModelStub:
        feature_names_ = BEHAVIOR_FEATURES

    async def load_ml_context(case_id: str):
        high_risk = case_id == "case-high_risk"
        return {
            "return_rate_pct": 0.5 if high_risk else 0.05,
            "customer_support_contacts": 0,
            "refund_to_order_ratio": 0.5 if high_risk else 0.05,
            "previous_dispute_count": 1 if high_risk else 0,
            "item_returned_opened": 0,
            "multiple_accounts_flag": 0,
            "refund_to_different_account": 0,
            "refund_amount_requested_usd": 49.99,
            "return_reason": "no_longer_needed",
            "address_change_before_delivery": 0,
        }

    def risk_probability(model, X):
        del model
        high_risk = float(X.iloc[0]["return_rate_pct"]) > 0.3
        probabilities = (
            {
                "legitimate": 0.1,
                "policy_abuser": 0.6,
                "fraudulent_return": 0.2,
                "wardrobing": 0.1,
            }
            if high_risk
            else {
                "legitimate": 0.95,
                "policy_abuser": 0.02,
                "fraudulent_return": 0.01,
                "wardrobing": 0.02,
            }
        )
        return [
            {
                "class_probabilities": probabilities,
                "predicted_class": max(probabilities, key=probabilities.get),
            }
        ]

    def analyze_image(photo_keys, *_):
        suspicious = any("suspicious" in key for key in photo_keys)
        return {
            "match": not suspicious,
            "similarilty": 0.42 if suspicious else 0.94,
            "fake_probabilty": suspicious,
            "vision_call": [],
        }

    monkeypatch.setattr(
        dependency,
        "get_policy_knowledge_base",
        lambda: PolicyKnowledgeBaseStub(),
    )
    monkeypatch.setattr(helper, "load_ml_context", load_ml_context)
    monkeypatch.setattr(agents, "_behavior_model", lambda: BehaviorModelStub())
    monkeypatch.setattr(agents, "risk_probability", risk_probability)
    monkeypatch.setattr(agents, "analyze_image", analyze_image)
