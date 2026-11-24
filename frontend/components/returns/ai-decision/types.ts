/**
 * TypeScript mirrors of the backend pipeline output types defined in
 * worker/pipeline/nodes/base.py. Field names match the Python models exactly
 * so we can safely cast agent_results from BackendReturn.
 *
 * Key typos are INTENTIONAL — they mirror the backend source:
 *   ImageResult.similarilty   (not "similarity")
 *   ImageResult.fake_probabilty (not "fake_probability")
 * Do NOT rename these fields; renaming would break the data mapping.
 */

// ─── Backend agent output shapes ─────────────────────────────────────────────

export interface GateResult {
  ok: boolean;
  reason: string;
}

export interface PlannerResult {
  next_steps: string[];
  skip: string[];
  reason: string;
}

export interface IntakeResult {
  status: "match" | "mismatch" | "missing_info";
  missing_fields: string[];
  notes: string;
}

export interface PolicyReference {
  document_id: string;
  policy_version: string;
  section: string;
  subsection: string | null;
  chunk_index: number;
}

export interface PolicyResult {
  eligible: boolean | "unclear";
  reason: string;
  policy_references: PolicyReference[];
}

export interface VisionAssessment {
  plausible: boolean | "unsure";
  confidence: number;
  observed_product: string;
  matches: string[];
  mismatches: string[];
  image_quality: "good" | "poor";
  note: string;
}

export interface ImageResult {
  match: boolean;
  // NOTE: These field names are intentionally misspelled to match the backend
  // source (worker/pipeline/nodes/base.py lines 103-104). Do not rename.
  similarilty: number;      // ← misspelled in backend, mirrored here
  fake_probabilty: boolean; // ← misspelled in backend, mirrored here
  vision_call: VisionAssessment[];
}

export type RiskClass =
  | "legitimate"
  | "policy_abuser"
  | "fraudulent_return"
  | "wardrobing";

export interface BehaviorResult {
  risk_score: number;
  predicted_class: RiskClass;
  class_probabilities: Record<RiskClass, number>;
  summary: string;
  features: Record<string, unknown>;
}

export interface DecisionProposal {
  proposal: "approve" | "deny" | "escalate";
  confidence: number;
  reasoning: string;
  risk_score: number;
  triggered_rules: string[];
  evidence: string[];
  requires_human_review: boolean;
}

export interface ExplanationResult {
  message: string;
}

/** One slot in the agent_results dict returned from /returns/review/:id */
export interface AgentResult {
  agent: string;
  output:
    | GateResult
    | PlannerResult
    | IntakeResult
    | PolicyResult
    | ImageResult
    | BehaviorResult
    | DecisionProposal
    | ExplanationResult
    | null;
  confidence: number | null;
  model: string | null;
  started_at: string;
  duration_ms: number;
  error: string | null;
  prompt_version: string | null;
}

/** The full agent_results dict: keys are agent names ("gate", "planner", …) */
export type AgentResultsDict = Record<string, AgentResult>;

// ─── View-model types (built by buildViewModel) ───────────────────────────────

/** Which step in the pipeline each UI row represents (display order). */
export type AgentName =
  | "gate"
  | "planner"
  | "intake"
  | "policy"
  | "image"
  | "behavior"
  | "decision"
  | "explanation";

/** Visual status of a pipeline step chip / row. */
export type StepStatus =
  | "ok"     // ran successfully
  | "warn"   // ran with a notable finding (mismatch, partial match, etc.)
  | "err"    // ran but threw an error
  | "stop"   // halted the workflow
  | "skip"   // planner deliberately skipped it
  | "notrun" // workflow stopped before reaching it
  | "pending"; // only used at runtime (not from API)

/** One row in the AGENT PIPELINE section. */
export interface AgentRow {
  name: AgentName;
  label: string;           // display name ("Gate", "Planner", …)
  status: StepStatus;
  summary: string;         // one-line description of what happened
  confidence: number | null;
  durationMs: number | null;
  error: string | null;    // non-null only when status === "err"
  hasDetail: boolean;      // whether a detail panel could be opened (future)
}

/** Outcome drives the decision display. */
export type Outcome =
  | "approve"
  | "deny"
  | "escalate"
  | "stopped"        // pipeline halted mid-way
  | "not_processed"; // agent_results is null / empty

/** The fully-computed view-model consumed by all UI sub-components. */
export interface AiDecisionViewModel {
  outcome: Outcome;

  // ── Top header ────────────────────────────────────────────────────
  proposalLabel: string;      // "Approve", "Deny", "Escalate", "Stopped", "Not processed"
  aiProposedDecision: string | null; // API-backed proposal summary for the return details card
  requiresHumanReview: boolean | null;
  promptMeta: string;          // e.g. "Prompt v3 · claude-sonnet · 6.4s total"

  // ── Metric cards (shown only when showMetrics is true) ───────────
  showMetrics: boolean;
  confidence: number | null;
  riskScore: number | null;
  riskLabel: "Low" | "Medium" | "High" | null;
  behaviorClass: string | null;      // e.g. "Legitimate"
  behaviorProbability: number | null; // e.g. 0.91

  // ── Reasoning & customer message ─────────────────────────────────
  reasoning: string;
  reasoningLabel: string;  // "Reasoning" or "Why it stopped"
  customerMessage: string | null; // draft message to customer

  // ── Rules & evidence ─────────────────────────────────────────────
  triggeredRules: string[];
  evidence: string[];

  // ── Pipeline step strip + rows ────────────────────────────────────
  steps: AgentRow[];        // 8 rows in display order
  stoppedAt: AgentName | null;
  totalDurationMs: number | null;

  // ── Stop notice (only when outcome === "stopped") ─────────────────
  notice: string | null;

}
