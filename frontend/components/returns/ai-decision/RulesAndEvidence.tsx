import React from "react";

interface RulesAndEvidenceProps {
  triggeredRules: string[];
  evidence: string[];
}

export function RulesAndEvidence({
  triggeredRules,
  evidence,
}: RulesAndEvidenceProps) {
  if (triggeredRules.length === 0 && evidence.length === 0) return null;

  return (
    <div className="space-y-4">
      {/* Triggered rules */}
      {triggeredRules.length > 0 && (
        <div>
          <h4 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
            Triggered Rules
          </h4>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {triggeredRules.map((rule) => (
              <span
                key={rule}
                className="inline-block rounded-md bg-[#F3F2ED] px-2 py-0.5 text-xs font-mono text-[#1F1E1B]"
              >
                {rule}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Evidence */}
      {evidence.length > 0 && (
        <div>
          <h4 className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
            Evidence
          </h4>
          <ul className="mt-1.5 space-y-1 text-xs text-[#1F1E1B]">
            {evidence.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="select-none text-[#9A988F]">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
