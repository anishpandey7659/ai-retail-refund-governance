import React from "react";

interface MetricCardsProps {
  confidence: number | null;
  riskScore: number | null;
  riskLabel: "Low" | "Medium" | "High" | null;
  behaviorClass: string | null;
  behaviorProbability: number | null;
}

export function MetricCards({
  confidence,
  riskScore,
  riskLabel,
  behaviorClass,
  behaviorProbability,
}: MetricCardsProps) {
  // Confidence bar color: green > 0.7, amber > 0.4, red else
  const confColor =
    confidence === null
      ? ""
      : confidence >= 0.7
        ? "bg-[#1E7A43]"
        : confidence >= 0.4
          ? "bg-[#8A5A00]"
          : "bg-[#B3261E]";

  // Risk bar color: low (<0.3) green, medium (0.3-0.6) amber, high (>0.6) red
  const riskColor =
    riskScore === null
      ? ""
      : riskScore < 0.3
        ? "bg-[#1E7A43]"
        : riskScore <= 0.6
          ? "bg-[#8A5A00]"
          : "bg-[#B3261E]";

  if (
    confidence === null &&
    riskScore === null &&
    behaviorClass === null &&
    behaviorProbability === null
  ) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {/* Confidence */}
      {confidence !== null && (
        <div className="rounded-xl bg-[#F3F2ED] p-3.5">
          <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
            Confidence
          </span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-[#1F1E1B]">
              {Math.round(confidence * 100)}%
            </span>
          </div>
          <div className="mt-2.5 h-1.5 w-full overflow-hidden rounded-full bg-[#E4E1D8]">
            <div
              className={`h-full rounded-full transition-all duration-300 ${confColor}`}
              style={{ width: `${Math.min(Math.max(confidence * 100, 0), 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Risk Score */}
      {riskScore !== null && (
        <div className="rounded-xl bg-[#F3F2ED] p-3.5">
          <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
            Risk score
          </span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-[#1F1E1B]">
              {riskScore.toFixed(2)}
            </span>
            {riskLabel && (
              <span className="text-xs font-semibold text-[#6B6A63]">
                {riskLabel}
              </span>
            )}
          </div>
          <div className="mt-2.5 h-1.5 w-full overflow-hidden rounded-full bg-[#E4E1D8]">
            <div
              className={`h-full rounded-full transition-all duration-300 ${riskColor}`}
              style={{ width: `${Math.min(Math.max(riskScore * 100, 0), 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Behavior Class */}
      {(behaviorClass !== null || behaviorProbability !== null) && (
        <div className="rounded-xl bg-[#F3F2ED] p-3.5">
          <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
            Behavior class
          </span>
          <div className="mt-1 flex items-baseline gap-2">
            {behaviorClass !== null && (
              <span className="truncate text-2xl font-bold tracking-tight text-[#1F1E1B]">
                {behaviorClass}
              </span>
            )}
            {behaviorProbability !== null && (
              <span className="text-xs font-semibold text-[#6B6A63]">
                {Math.round(behaviorProbability * 100)}%
              </span>
            )}
          </div>
          <div className="mt-2.5 h-1.5 w-full rounded-full bg-transparent" />
        </div>
      )}
    </div>
  );
}
