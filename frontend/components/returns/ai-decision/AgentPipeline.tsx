import React from "react";
import {
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  StopCircle,
  MinusCircle,
} from "lucide-react";
import type { AgentRow, StepStatus } from "./types";
import { formatDuration } from "./buildViewModel";

interface AgentPipelineProps {
  steps: AgentRow[];
  totalDurationMs: number | null;
  stoppedAt: string | null;
}

function getStatusIcon(status: StepStatus) {
  switch (status) {
    case "ok":
      return <CheckCircle2 size={16} className="text-[#1E7A43]" />;
    case "warn":
      return <AlertTriangle size={16} className="text-[#8A5A00]" />;
    case "err":
      return <AlertCircle size={16} className="text-[#B3261E]" />;
    case "stop":
      return <StopCircle size={16} className="text-[#B3261E]" />;
    case "skip":
    case "notrun":
    default:
      return <MinusCircle size={16} className="text-[#9A988F]" />;
  }
}

export function AgentPipeline({
  steps,
  totalDurationMs,
  stoppedAt,
}: AgentPipelineProps) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between border-b border-[#E6E3DA] pb-2">
        <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
          Agent Pipeline
        </span>
        {totalDurationMs !== null && (
          <span className="text-xs text-[#9A988F]">
            {stoppedAt
              ? `Stopped after ${formatDuration(totalDurationMs)}`
              : `Total ${formatDuration(totalDurationMs)}`}
          </span>
        )}
      </div>

      <div className="divide-y divide-[#E6E3DA]">
        {steps.map((step) => {
          const isMuted = step.status === "skip" || step.status === "notrun";
          const isError = step.status === "err";
          const isStop = step.status === "stop";

          return (
            <div
              key={step.name}
              className={`flex items-center gap-3 px-2 py-2.5 transition-colors ${
                isStop
                  ? "bg-[#FFF8F7] -mx-2 px-4 rounded-md"
                  : isError
                    ? "bg-[#FFF8F7] -mx-2 px-4 rounded-md"
                    : "hover:bg-[#FAF9F5]"
              }`}
            >
              {/* Status Icon */}
              <div className="flex-shrink-0">{getStatusIcon(step.status)}</div>

              {/* Agent Name */}
              <div
                className={`w-24 flex-shrink-0 text-xs font-semibold ${
                  isMuted ? "text-[#9A988F]" : "text-[#1F1E1B]"
                }`}
              >
                {step.label}
              </div>

              {/* Summary / Error */}
              <div className="min-w-0 flex-1 text-xs">
                {isError ? (
                  <span className="font-medium text-[#B3261E]">
                    {step.error || step.summary}
                  </span>
                ) : (
                  <span
                    className={`truncate block ${
                      isMuted ? "text-[#9A988F]" : "text-[#1F1E1B]"
                    }`}
                  >
                    {step.summary}
                  </span>
                )}
              </div>

              {/* Confidence % */}
              <div className="w-12 text-right text-xs text-[#6B6A63] tabular-nums flex-shrink-0">
                {step.confidence !== null
                  ? `${Math.round(step.confidence * 100)}%`
                  : ""}
              </div>

              {/* Duration */}
              <div className="w-20 text-right text-xs tabular-nums flex-shrink-0">
                {step.durationMs !== null && (
                  <span className="text-[#9A988F]">
                    {formatDuration(step.durationMs)}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
