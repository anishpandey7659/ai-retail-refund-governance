import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { buildViewModel } from "../buildViewModel";
import {
  fixtureApprove,
  fixtureEscalate,
  fixtureDeny,
  fixtureGateStop,
  fixtureIntakeStop,
  fixturePolicyUnclear,
} from "../fixtures";
import type { BackendReturn } from "@/lib/retail-api";

// Pure TypeScript test suite that runs with Node test runner or any runner
describe("buildViewModel", () => {
  it("State 1: Approve proposal", () => {
    const vm = buildViewModel(fixtureApprove);
    assert.equal(vm.outcome, "approve");
    assert.equal(vm.showMetrics, true);
    assert.equal(vm.stoppedAt, null);
    assert.match(vm.aiProposedDecision ?? "", /^Approve · 87%/);
    assert.equal(vm.requiresHumanReview, true);
    assert.equal(vm.confidence, 0.87);
    assert.equal(vm.riskScore, 0.12);
    assert.equal(vm.riskLabel, "Low");
    assert.equal(vm.steps.length, 8);
    // Behavior skipped by planner
    const behaviorStep = vm.steps.find((s) => s.name === "behavior");
    assert.equal(behaviorStep?.status, "skip");
  });

  it("State 2: Escalate proposal with explanation agent error", () => {
    const vm = buildViewModel(fixtureEscalate);
    assert.equal(vm.outcome, "escalate");
    assert.equal(vm.showMetrics, true);
    assert.match(vm.aiProposedDecision ?? "", /^Escalate · 58%/);
    assert.equal(vm.riskScore, 0.64);
    assert.equal(vm.riskLabel, "High");
    assert.equal(vm.steps.length, 8);
    // Explanation step should be in err status
    const explStep = vm.steps.find((s) => s.name === "explanation");
    assert.equal(explStep?.status, "err");
    assert.match(explStep?.error ?? "", /Failed: request timed out/);
    assert.equal(vm.customerMessage, null);
  });

  it("State 3: Deny proposal", () => {
    const vm = buildViewModel(fixtureDeny);
    assert.equal(vm.outcome, "deny");
    assert.equal(vm.showMetrics, true);
    assert.match(vm.aiProposedDecision ?? "", /^Deny · 92%/);
    assert.equal(vm.riskScore, 0.88);
    assert.equal(vm.riskLabel, "High");
    assert.equal(vm.steps.length, 8);
    // Image skipped
    const imgStep = vm.steps.find((s) => s.name === "image");
    assert.equal(imgStep?.status, "skip");
  });

  it("State 4: Gate stop", () => {
    const vm = buildViewModel(fixtureGateStop);
    assert.equal(vm.outcome, "stopped");
    assert.equal(vm.stoppedAt, "gate");
    assert.equal(vm.showMetrics, false);
    assert.equal(vm.aiProposedDecision, null);
    assert.match(vm.notice ?? "", /Photo evidence is mandatory/);
    // Subsequent steps should be notrun
    const plannerStep = vm.steps.find((s) => s.name === "planner");
    assert.equal(plannerStep?.status, "notrun");
  });

  it("State 5: Intake stop", () => {
    const vm = buildViewModel(fixtureIntakeStop);
    assert.equal(vm.outcome, "stopped");
    assert.equal(vm.stoppedAt, "intake");
    assert.equal(vm.showMetrics, false);
    assert.equal(vm.aiProposedDecision, null);
    assert.match(vm.notice ?? "", /Mismatch/);
  });

  it("State 6: Policy unclear stop", () => {
    const vm = buildViewModel(fixturePolicyUnclear);
    assert.equal(vm.outcome, "stopped");
    assert.equal(vm.stoppedAt, "policy");
    assert.equal(vm.showMetrics, false);
    assert.equal(vm.aiProposedDecision, null);
    assert.match(vm.notice ?? "", /Manufacturer revised fabric composition/);
  });

  it("Handles null or empty agent_results safely", () => {
    const emptyReturn: BackendReturn = {
      id: "empty-test",
      order_id: "1",
      order_item_id: "1",
      reason_code: "defective",
      reason_text: "test",
      status: "pending",
      amount: 10,
      final_decision: null,
      created_at: "2026-01-01T00:00:00Z",
      photo_urls: [],
      agent_results: null,
    };
    const vm = buildViewModel(emptyReturn);
    assert.equal(vm.outcome, "not_processed");
    assert.equal(vm.showMetrics, false);
    assert.equal(vm.aiProposedDecision, null);
    assert.equal(vm.requiresHumanReview, null);
    assert.equal(vm.steps.length, 8);
  });

  it("does not invent a duration when the API omits agent durations", () => {
    const returnWithoutDurations: BackendReturn = {
      ...fixtureApprove,
      agent_results: {
        decision: {
          output: {
            proposal: "approve",
            risk_score: 0.12,
            triggered_rules: [],
            evidence: [],
            requires_human_review: true,
          },
        },
      },
    };

    const vm = buildViewModel(returnWithoutDurations);
    assert.equal(vm.totalDurationMs, null);
    assert.equal(vm.promptMeta, "");
    assert.equal(vm.aiProposedDecision, "Approve");
    assert.equal(vm.confidence, null);
  });

  it("uses the human-review requirement returned by the API", () => {
    const returnWithoutHumanReview: BackendReturn = {
      ...fixtureApprove,
      agent_results: {
        decision: {
          output: {
            proposal: "approve",
            requires_human_review: false,
          },
        },
      },
    };

    assert.equal(
      buildViewModel(returnWithoutHumanReview).requiresHumanReview,
      false,
    );
  });
});
