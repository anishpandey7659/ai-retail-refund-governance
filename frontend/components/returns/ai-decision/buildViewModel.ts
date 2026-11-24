/**
 * buildViewModel — pure function that transforms a BackendReturn into the
 * AiDecisionViewModel consumed by all AI decision UI components.
 *
 * Rules:
 * - Never throws. All agent outputs are treated as potentially null/missing.
 * - Derives "stoppedAt" from agent output signals, not from DB status.
 * - Maps the 8-agent pipeline in canonical display order.
 */

import type { BackendReturn } from "@/lib/retail-api";
import type {
  AgentName,
  AgentResult,
  AgentResultsDict,
  AgentRow,
  AiDecisionViewModel,
  BehaviorResult,
  DecisionProposal,
  ExplanationResult,
  GateResult,
  IntakeResult,
  Outcome,
  PolicyResult,
  StepStatus,
} from "./types";

// ─── Constants ────────────────────────────────────────────────────────────────

const AGENT_DISPLAY_ORDER: AgentName[] = [
  "gate",
  "planner",
  "intake",
  "policy",
  "image",
  "behavior",
  "decision",
  "explanation",
];

const AGENT_LABELS: Record<AgentName, string> = {
  gate: "Gate",
  planner: "Planner",
  intake: "Intake",
  policy: "Policy",
  image: "Image",
  behavior: "Behavior",
  decision: "Decision",
  explanation: "Explanation",
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Format milliseconds as "1.2s" (1 dp < 10 s, else rounded "12s"). */
export function formatDuration(ms: number | null): string {
  if (ms === null) return "—";
  const s = ms / 1000;
  if (s < 10) return `${s.toFixed(1)}s`;
  return `${Math.round(s)}s`;
}

/** Capitalise first letter, replace underscores with spaces. */
function humanise(s: string): string {
  if (!s) return s;
  return s.charAt(0).toUpperCase() + s.slice(1).replaceAll("_", " ");
}

/** Safely cast agent output to a typed shape (returns null if keys don't match). */
function asOutput<T>(output: unknown, key: keyof T): T | null {
  if (typeof output === "object" && output !== null && key in output) {
    return output as T;
  }
  return null;
}

/** Determine which agent halted the workflow (before the decision ran). */
function findStoppedAt(
  dict: AgentResultsDict,
): AgentName | null {
  // Decision ran → no stop (even if intake/policy had issues they're shown as warn)
  const decisionRan = dict["decision"] != null;
  if (decisionRan) return null;

  // Gate: ok === false
  const gate = dict["gate"];
  if (gate) {
    const g = asOutput<GateResult>(gate.output, "ok");
    if (g && g.ok === false) return "gate";
  }

  // Intake: status !== "match" and decision didn't run
  const intake = dict["intake"];
  if (intake) {
    const i = asOutput<IntakeResult>(intake.output, "status");
    if (i && i.status !== "match") return "intake";
  }

  // Policy: eligible !== true (could be false or "unclear") and decision didn't run
  const policy = dict["policy"];
  if (policy) {
    const p = asOutput<PolicyResult>(policy.output, "eligible");
    if (p && p.eligible !== true) return "policy";
  }

  return null;
}

/** Derive per-agent step status. */
function deriveStepStatus(
  name: AgentName,
  result: AgentResult | undefined,
  stoppedAt: AgentName | null,
  skipList: string[],
): StepStatus {
  // Explicitly skipped by planner
  if (skipList.includes(name)) return "skip";

  // Not in results at all
  if (!result) {
    return "notrun";
  }

  // Error
  if (result.error) return "err";

  // This is the stopping agent
  if (stoppedAt === name) return "stop";

  // Per-agent warn signals (when decision DID run so it's warn, not stop)
  if (name === "intake") {
    const i = asOutput<IntakeResult>(result.output, "status");
    if (i && i.status !== "match") return "warn";
  }
  if (name === "policy") {
    const p = asOutput<PolicyResult>(result.output, "eligible");
    if (p && p.eligible !== true) return "warn";
  }
  if (name === "image") {
    const img = result.output as { match?: boolean } | null;
    if (img && img.match === false) return "warn";
  }

  return "ok";
}

/** Build a one-line summary string for each agent row. */
function buildSummary(
  name: AgentName,
  result: AgentResult | undefined,
  status: StepStatus,
): string {
  if (status === "skip") return "Skipped by planner";
  if (status === "notrun") return "Not run";
  if (!result) return "—";
  if (result.error) return result.error;

  switch (name) {
    case "gate": {
      const g = asOutput<GateResult>(result.output, "ok");
      return g ? (g.ok ? "Passed" : `Stopped: ${g.reason}`) : result.error ?? "—";
    }
    case "planner": {
      const p = result.output as { reason?: string } | null;
      return p?.reason ?? "—";
    }
    case "intake": {
      const i = asOutput<IntakeResult>(result.output, "status");
      if (!i) return "—";
      if (i.status === "match") return "Match";
      if (i.status === "mismatch") return i.notes ? `Mismatch: ${i.notes}` : "Mismatch";
      return i.missing_fields.length
        ? `Missing info: ${i.missing_fields.join(", ")}`
        : i.notes
          ? `Missing info: ${i.notes}`
          : "Missing info";
    }
    case "policy": {
      const p = asOutput<PolicyResult>(result.output, "eligible");
      if (!p) return "—";
      if (p.eligible === true) return `Eligible, ${p.policy_references.length} policy reference${p.policy_references.length !== 1 ? "s" : ""}`;
      if (p.eligible === "unclear") return `Unclear, ${p.policy_references.length} policy reference`;
      return `Not eligible: ${p.reason}`;
    }
    case "image": {
      const img = result.output as { match?: boolean; similarilty?: number; fake_probabilty?: boolean } | null;
      if (!img) return "—";
      // Note: "similarilty" is intentionally misspelled (mirrors backend)
      const sim = img.similarilty != null ? `similarity ${img.similarilty.toFixed(2)}` : "";
      if (img.match === undefined) return sim || "—";
      return [img.match ? "Match" : "Partial match", sim]
        .filter(Boolean)
        .join(", ");
    }
    case "behavior": {
      const b = asOutput<BehaviorResult>(result.output, "predicted_class");
      if (!b) return "—";
      return `${humanise(b.predicted_class)}, risk ${b.risk_score.toFixed(2)}`;
    }
    case "decision": {
      const d = asOutput<DecisionProposal>(result.output, "proposal");
      if (!d) return "—";
      return humanise(d.proposal);
    }
    case "explanation": {
      const e = asOutput<ExplanationResult>(result.output, "message");
      return e ? "Message crafted" : "—";
    }
    default:
      return "—";
  }
}

// ─── Main function ────────────────────────────────────────────────────────────

export function buildViewModel(ret: BackendReturn): AiDecisionViewModel {
  const raw = ret.agent_results as AgentResultsDict | null | undefined;

  // ── Not processed ────────────────────────────────────────────────────────
  if (!raw || Object.keys(raw).length === 0) {
    return {
      outcome: "not_processed",
      proposalLabel: "Not processed",
      aiProposedDecision: null,
      requiresHumanReview: null,
      promptMeta: "",
      showMetrics: false,
      confidence: null,
      riskScore: null,
      riskLabel: null,
      behaviorClass: null,
      behaviorProbability: null,
      reasoning: "",
      reasoningLabel: "Reasoning",
      customerMessage: null,
      triggeredRules: [],
      evidence: [],
      steps: AGENT_DISPLAY_ORDER.map((name) => ({
        name,
        label: AGENT_LABELS[name],
        status: "notrun",
        summary: "Not run",
        confidence: null,
        durationMs: null,
        error: null,
        hasDetail: false,
      })),
      stoppedAt: null,
      totalDurationMs: null,
      notice: null,
    };
  }

  // ── Derive stop point ────────────────────────────────────────────────────
  const stoppedAt = findStoppedAt(raw);

  // ── Planner skip list ────────────────────────────────────────────────────
  const plannerOut = raw["planner"]?.output as { skip?: string[] } | null;
  const skipList: string[] = plannerOut?.skip ?? [];

  // ── Build steps ──────────────────────────────────────────────────────────
  const steps: AgentRow[] = AGENT_DISPLAY_ORDER.map((name) => {
    const result = raw[name];
    const status = deriveStepStatus(name, result, stoppedAt, skipList);
    const summary = buildSummary(name, result, status);
    return {
      name,
      label: AGENT_LABELS[name],
      status,
      summary,
      confidence: result?.confidence ?? null,
      durationMs: result?.duration_ms ?? null,
      error: result?.error ?? null,
      hasDetail: false,
    };
  });

  // ── Total duration ───────────────────────────────────────────────────────
  const durations = Object.values(raw)
    .map((result) => result?.duration_ms)
    .filter((duration): duration is number => typeof duration === "number");
  const totalDurationMs =
    durations.length > 0
      ? durations.reduce((sum, duration) => sum + duration, 0)
      : null;

  // ── Decision output ──────────────────────────────────────────────────────
  const decisionResult = raw["decision"];
  const decision = asOutput<DecisionProposal>(decisionResult?.output, "proposal");

  // ── Outcome ───────────────────────────────────────────────────────────────
  let outcome: Outcome;
  if (stoppedAt) {
    outcome = "stopped";
  } else if (decision) {
    outcome = decision.proposal; // "approve" | "deny" | "escalate"
  } else {
    outcome = "not_processed";
  }

  // ── Proposal label ────────────────────────────────────────────────────────
  const proposalLabel = decision
    ? humanise(decision.proposal)
    : stoppedAt
      ? "Stopped"
      : "Not processed";

  // ── aiProposedDecision string (shown in return details card) ─────────────
  const confidence =
    typeof decision?.confidence === "number" ? decision.confidence : null;
  const aiProposedDecision = decision
    ? `${humanise(decision.proposal)}${confidence !== null ? ` · ${Math.round(confidence * 100)}%` : ""}`
    : null;
  const requiresHumanReview = decision?.requires_human_review ?? null;

  // ── Prompt meta ──────────────────────────────────────────────────────────
  const decisionModel = decisionResult?.model ?? null;
  const promptVersion = decisionResult?.prompt_version ?? null;
  const totalSecs = formatDuration(totalDurationMs);
  const metaParts = [
    promptVersion ? `Prompt ${promptVersion}` : null,
    decisionModel,
    totalDurationMs !== null ? `${totalSecs} total` : null,
  ].filter(Boolean);
  const promptMeta = metaParts.join(" · ");

  // ── Metrics ──────────────────────────────────────────────────────────────
  const showMetrics = outcome !== "stopped" && outcome !== "not_processed";
  const riskScore = decision?.risk_score ?? null;
  let riskLabel: "Low" | "Medium" | "High" | null = null;
  if (riskScore !== null) {
    riskLabel = riskScore < 0.3 ? "Low" : riskScore < 0.6 ? "Medium" : "High";
  }

  const behaviorResult = raw["behavior"];
  const behavior = asOutput<BehaviorResult>(behaviorResult?.output, "predicted_class");
  const behaviorClass = behavior ? humanise(behavior.predicted_class) : null;
  const behaviorProbability =
    behavior && behavior.predicted_class
      ? (behavior.class_probabilities?.[behavior.predicted_class] ?? null)
      : null;

  // ── Reasoning ─────────────────────────────────────────────────────────────
  const reasoning = decision?.reasoning ?? "";
  const reasoningLabel = stoppedAt ? "Why it stopped" : "Reasoning";

  // ── Customer message ──────────────────────────────────────────────────────
  const explResult = raw["explanation"];
  const expl = asOutput<ExplanationResult>(explResult?.output, "message");
  const customerMessage = expl?.message ?? null;

  // ── Rules & evidence ──────────────────────────────────────────────────────
  const triggeredRules = decision?.triggered_rules ?? [];
  const evidence = decision?.evidence ?? [];

  // ── Stop notice ───────────────────────────────────────────────────────────
  let notice: string | null = null;
  if (stoppedAt === "gate") {
    const g = asOutput<GateResult>(raw["gate"]?.output, "ok");
    notice = g?.reason ?? null;
  } else if (stoppedAt === "intake") {
    const i = asOutput<IntakeResult>(raw["intake"]?.output, "status");
    notice = i
      ? i.status === "mismatch"
        ? `Mismatch: ${i.notes}`.trim()
        : i.status === "missing_info"
          ? [i.notes, ...i.missing_fields].filter(Boolean).join(": ") || null
          : null
      : null;
  } else if (stoppedAt === "policy") {
    const p = asOutput<PolicyResult>(raw["policy"]?.output, "eligible");
    notice =
      p?.reason
        ? p.eligible === "unclear"
          ? `Policy unclear: ${p.reason}`
          : p.reason
        : null;
  }

  return {
    outcome,
    proposalLabel,
    aiProposedDecision,
    requiresHumanReview,
    promptMeta,
    showMetrics,
    confidence,
    riskScore,
    riskLabel,
    behaviorClass,
    behaviorProbability,
    reasoning,
    reasoningLabel,
    customerMessage,
    triggeredRules,
    evidence,
    steps,
    stoppedAt,
    totalDurationMs,
    notice,
  };
}
