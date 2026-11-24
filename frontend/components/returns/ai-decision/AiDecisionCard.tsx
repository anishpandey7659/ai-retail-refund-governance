import React from "react";
import type { BackendReturn } from "@/lib/retail-api";
import { buildViewModel } from "./buildViewModel";
import { ProposalHeader } from "./ProposalHeader";
import { WorkflowStepStrip } from "./WorkflowStepStrip";
import { MetricCards } from "./MetricCards";
import { ReasoningAndMessage } from "./ReasoningAndMessage";
import { RulesAndEvidence } from "./RulesAndEvidence";
import { AgentPipeline } from "./AgentPipeline";
import { AlertCircle } from "lucide-react";

interface AiDecisionCardProps {
  returnRecord: BackendReturn;
}

export function AiDecisionCard({ returnRecord }: AiDecisionCardProps) {
  const vm = buildViewModel(returnRecord);

  if (vm.outcome === "not_processed") {
    return (
      <section className="rounded-2xl border border-[#E6E3DA] bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 text-sm text-[#6B6A63]">
          <AlertCircle size={16} />
          <span>The AI decision pipeline has not processed this return request yet.</span>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-[#E6E3DA] bg-white p-6 shadow-sm space-y-5">
      {/* 1. Header with API-backed proposal, human review tag, and prompt metadata */}
      <ProposalHeader
        outcome={vm.outcome}
        label={vm.proposalLabel}
        requiresHumanReview={vm.requiresHumanReview}
        promptMeta={vm.promptMeta}
      />

      {/* 2. Pipeline step strip */}
      <WorkflowStepStrip steps={vm.steps} />

      {/* Notice alert when pipeline stopped early */}
      {vm.notice && (
        <div className="rounded-xl border border-[#F1C4BF] bg-[#FFF8F7] p-3 text-xs text-[#B3261E] flex items-start gap-2">
          <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold">Workflow stopped: </span>
            {vm.notice}
          </div>
        </div>
      )}

      {/* 3. Metric cards (confidence, risk, behavior class) */}
      {vm.showMetrics && (
        <MetricCards
          confidence={vm.confidence}
          riskScore={vm.riskScore}
          riskLabel={vm.riskLabel}
          behaviorClass={vm.behaviorClass}
          behaviorProbability={vm.behaviorProbability}
        />
      )}

      {/* 4. Reasoning / customer message (left) & Triggered rules / evidence (right) */}
      {(vm.reasoning ||
        vm.customerMessage ||
        vm.triggeredRules.length > 0 ||
        vm.evidence.length > 0) && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 pt-1">
          <ReasoningAndMessage
            reasoning={vm.reasoning}
            reasoningLabel={vm.reasoningLabel}
            customerMessage={vm.customerMessage}
          />
          <RulesAndEvidence
            triggeredRules={vm.triggeredRules}
            evidence={vm.evidence}
          />
        </div>
      )}

      {/* 5. Agent Pipeline table */}
      <AgentPipeline
        steps={vm.steps}
        totalDurationMs={vm.totalDurationMs}
        stoppedAt={vm.stoppedAt}
      />
    </section>
  );
}
