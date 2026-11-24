import React from "react";
import { CheckCircle2, ArrowUpRight, AlertCircle, Ban } from "lucide-react";
import type { Outcome } from "./types";

interface ProposalHeaderProps {
  outcome: Outcome;
  label: string;
  requiresHumanReview: boolean | null;
  promptMeta: string;
}

export function ProposalHeader({
  outcome,
  label,
  requiresHumanReview,
  promptMeta,
}: ProposalHeaderProps) {
  // Pill styles based on outcome
  const badgeConfig = {
    approve: {
      bg: "bg-[#E4F3E9]",
      text: "text-[#1E7A43]",
      icon: <CheckCircle2 size={16} className="text-[#1E7A43]" />,
    },
    escalate: {
      bg: "bg-[#FBF0D6]",
      text: "text-[#8A5A00]",
      icon: <ArrowUpRight size={16} className="text-[#8A5A00]" />,
    },
    deny: {
      bg: "bg-[#FCE8E6]",
      text: "text-[#B3261E]",
      icon: <Ban size={16} className="text-[#B3261E]" />,
    },
    stopped: {
      bg: "bg-[#F3F2ED]",
      text: "text-[#6B6A63]",
      icon: <AlertCircle size={16} className="text-[#6B6A63]" />,
    },
    not_processed: {
      bg: "bg-[#F3F2ED]",
      text: "text-[#6B6A63]",
      icon: <AlertCircle size={16} className="text-[#6B6A63]" />,
    },
  }[outcome];

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
          AI Proposed Decision
        </span>
        {requiresHumanReview !== null && (
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold tracking-tight ${
              requiresHumanReview
                ? "bg-[#FBF0D6] text-[#8A5A00]"
                : "bg-[#F3F2ED] text-[#6B6A63]"
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                requiresHumanReview ? "bg-[#8A5A00]" : "bg-[#6B6A63]"
              }`}
            />
            Human review {requiresHumanReview ? "required" : "not required"}
          </span>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div
          className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-sm font-semibold ${badgeConfig.bg} ${badgeConfig.text}`}
        >
          {badgeConfig.icon}
          <span>{label}</span>
        </div>

        {promptMeta && (
          <span className="text-xs text-[#9A988F] font-mono sm:text-right">
            {promptMeta}
          </span>
        )}
      </div>
    </div>
  );
}
