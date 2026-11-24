import React from "react";

interface ReasoningAndMessageProps {
  reasoning: string;
  reasoningLabel: string;
  customerMessage: string | null;
}

export function ReasoningAndMessage({
  reasoning,
  reasoningLabel,
  customerMessage,
}: ReasoningAndMessageProps) {
  return (
    <div className="space-y-4">
      {/* Reasoning section */}
      {reasoning && (
        <div>
          <h4 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
            {reasoningLabel}
          </h4>
          <p className="mt-1 text-sm leading-relaxed text-[#1F1E1B]">
            {reasoning}
          </p>
        </div>
      )}

      {/* Customer message draft */}
      {customerMessage && (
        <div>
          <h4 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
            Message to Customer
          </h4>
          <div className="mt-1.5 rounded-lg bg-[#F3F2ED] p-3 text-sm leading-relaxed">
            <span className="text-[#1F1E1B]">{customerMessage}</span>
          </div>
        </div>
      )}
    </div>
  );
}
