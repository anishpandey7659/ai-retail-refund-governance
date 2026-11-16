from typing import Any, Literal, Optional, get_args

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ------------------------------------------------------------------
# ENUMS / LITERALS
# ------------------------------------------------------------------

ReasonCode = Literal[
    "damaged",
    "not_as_described",
    "wrong_item",
    "no_longer_needed",
    "defective",
    "arrived_late",
    "quality",
]

CaseStatus = Literal[
    "pending",
    "in_review",
    "escalated",
    "approved",
    "denied",
    "refunded",
]

VALID_REASON_CODES = frozenset(get_args(ReasonCode))
VALID_CASE_STATUSES = frozenset(get_args(CaseStatus))

PHOTO_REQUIRED: frozenset[ReasonCode] = frozenset({
    "damaged",
    "defective",
    "not_as_described",
    "wrong_item",
})
MIN_PRIOR_RETURNS = 1
HIGH_RETURN_RATE = 0.3

# ------------------------------------------------------------------
# NESTED SCHEMAS
# ------------------------------------------------------------------

class GateResult(BaseModel):
    ok: bool
    reason: str


AgentStep = Literal[
    "intake",
    "policy",
    "image",
    "behavior",
    "decision",
    "critic",
    "explanation",
]
SkippedAgentStep = Literal["image", "behavior"]


class PlannerResult(BaseModel):
    next_steps: list[AgentStep]
    skip: list[SkippedAgentStep]
    reason: str


class IntakeResult(BaseModel):
    status: Literal["match", "mismatch", "missing_info"]
    missing_fields: list[str]
    notes: str


IntakeVerdict = IntakeResult


class PolicyReference(BaseModel):
    document_id: str
    policy_version: str
    section: str
    subsection: Optional[str]
    chunk_index: int


class PolicyResult(BaseModel):
    eligible: bool | Literal["unclear"]
    reason: str
    policy_references: list[PolicyReference]


class VisionAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plausible: bool | Literal["unsure"]
    confidence: float = Field(ge=0, le=1)
    observed_product: str
    matches: list[str]
    mismatches: list[str]
    image_quality: Literal["good", "poor"]
    note: str


class ImageResult(BaseModel):
    match: bool
    similarilty: float = Field(ge=0, le=1)
    fake_probabilty: bool
    vision_call: list[VisionAssessment]


RiskClass = Literal[
    "legitimate",
    "policy_abuser",
    "fraudulent_return",
    "wardrobing",
]


class BehaviorResult(BaseModel):
    risk_score: float = Field(ge=0, le=1, allow_inf_nan=False)
    predicted_class: RiskClass
    class_probabilities: dict[RiskClass, float]
    summary: str
    features: dict[str, Any]


class DecisionCaseFacts(BaseModel):
    case_id: str
    item_name: str
    reason_code: ReasonCode
    description: str | None = None
    product_title: str | None = None
    product_category: str | None = None
    return_amount: float | None = None
    high_value_threshold: float = Field(default=250, gt=0)
    photos_present: bool
    image_verification_required: bool
    behavior_verification_required: bool
    prior_returns: int = 0
    prior_denials: int = 0
    ring_linked: bool = False
    linked_accounts: int | None = None


class DecisionInput(BaseModel):
    gate_result: GateResult | None = None
    planner_result: PlannerResult | None = None
    intake_result: IntakeResult | None = None
    policy_result: PolicyResult | None = None
    image_result: ImageResult | None = None
    behavior_result: BehaviorResult | None = None
    case_facts: DecisionCaseFacts


class DecisionProposal(BaseModel):
    proposal: Literal["approve", "deny", "escalate"]
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    reasoning: str
    risk_score: float = Field(ge=0, le=1, allow_inf_nan=False)
    triggered_rules: list[str]
    evidence: list[str]
    requires_human_review: bool

    @model_validator(mode="after")
    def escalation_requires_review(self) -> "DecisionProposal":
        if self.proposal == "escalate" and not self.requires_human_review:
            raise ValueError("Escalation proposals must require human review.")
        return self


class ExplanationInput(BaseModel):
    proposal: Literal["approve", "deny", "escalate"]
    requires_human_review: bool
    product_name: str
    reason_code: ReasonCode
    key_reasons: list[str]


class ExplanationResult(BaseModel):
    message: str = Field(min_length=1)


AgentOutput = (
    GateResult
    | PlannerResult
    | IntakeResult
    | PolicyResult
    | ImageResult
    | BehaviorResult
    | DecisionProposal
    | ExplanationResult
)


class AgentResult(BaseModel):
    agent: str
    output: Optional[AgentOutput]
    confidence: Optional[float]
    model: Optional[str]
    started_at: str
    duration_ms: int
    error: Optional[str]
    prompt_version: str | None = None


class ProductInfo(BaseModel):
    product_id: str
    title: str
    description: str
    category: str
    current_price: float
    image_key: Optional[str]


class PhotoInfo(BaseModel):
    id: str
    object_key: str
    content_type: str
    bytes: int

class OrderInfo(BaseModel):
    order_item_id: int
    quantity: int
    price_at_purchase: float
    return_amount: float
    delivered_at: Optional[str] = None


class CustomerHistory(BaseModel):
    orders: int = 0
    returns: int = 0
    approved: int = 0
    denied: int = 0
    return_rate: float = 0.0

# ------------------------------------------------------------------
# MAIN CASE SCHEMA
# ------------------------------------------------------------------

class Case(BaseModel):

    # Identity
    case_id: str
    order_id: int
    customer_id: str
    return_request_at: str

    # Customer submission
    item_name: str
    reason_code: ReasonCode
    description: Optional[str] = None
    photos: list[PhotoInfo] = Field(default_factory=list)

    # Customer history (prior returns only; excludes this one)
    customer_history: CustomerHistory = Field(default_factory=CustomerHistory)

    # Backend-enriched information
    product_info: Optional[ProductInfo] = None
    order_info: Optional[OrderInfo] = None

    # Pipeline state
    status: CaseStatus = "pending"
    gate_result: Optional[GateResult] = None

    # Agent execution results
    agent_results: dict[str, AgentResult] = Field(default_factory=dict)
