import React from "react";
import { Check, Octagon, Minus, AlertTriangle, AlertCircle } from "lucide-react";
import type { AgentRow, StepStatus } from "./types";

interface WorkflowStepStripProps {
  steps: AgentRow[];
}

function getStepIcon(status: StepStatus) {
  switch (status) {
    case "ok":
      return <Check size={12} className="text-[#1E7A43]" />;
    case "warn":
      return <AlertTriangle size={12} className="text-[#8A5A00]" />;
    case "err":
      return <AlertCircle size={12} className="text-[#B3261E]" />;
    case "stop":
      return <Octagon size={12} className="text-[#B3261E]" />;
    case "skip":
    case "notrun":
    default:
      return <Minus size={12} className="text-[#9A988F]" />;
  }
}

function getChipStyle(status: StepStatus) {
  switch (status) {
    case "ok":
      return "bg-[#F3F2ED] text-[#1F1E1B] border-transparent font-medium";
    case "warn":
      return "bg-[#FBF0D6] text-[#8A5A00] border-[#E8DEC0] font-medium";
    case "err":
      return "bg-[#FCE8E6] text-[#B3261E] border-[#F1C4BF] font-medium";
    case "stop":
      return "bg-[#FCE8E6] text-[#B3261E] border-[#F1C4BF] font-semibold";
    case "skip":
    case "notrun":
    default:
      return "bg-transparent text-[#9A988F] border-[#E6E3DA] font-normal";
  }
}

export function WorkflowStepStrip({ steps }: WorkflowStepStripProps) {
  return (
    <div className="flex flex-wrap items-center gap-1.5 py-1">
      {steps.map((step, idx) => (
        <React.Fragment key={step.name}>
          <div
            className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs transition-colors ${getChipStyle(
              step.status,
            )}`}
          >
            {getStepIcon(step.status)}
            <span>{step.label}</span>
          </div>
          {idx < steps.length - 1 && (
            <span className="text-xs text-[#CFCBC0] select-none">›</span>
          )}
        </React.Fragment>
      ))}
    </div>
  );
}
