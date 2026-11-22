import React from "react";
import { type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  detail: string;
  icon: LucideIcon;
  accent?: string;
  className?: string;
}

export function StatCard({
  label,
  value,
  detail,
  icon: Icon,
  accent = "bg-[#F1F0EC] text-[#555048]",
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-[#E8E6E1] bg-white p-5 shadow-[0_1px_2px_rgba(0,0,0,0.02)] transition-shadow hover:shadow-[0_4px_12px_rgba(0,0,0,0.03)]",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <span className="text-xs font-medium uppercase tracking-[0.08em] text-[#77746E]">
            {label}
          </span>
          <div className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[#252525] tabular-nums">
            {value}
          </div>
        </div>
        <div
          className={cn(
            "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl",
            accent,
          )}
        >
          <Icon size={19} />
        </div>
      </div>
      <div className="mt-4 flex items-center gap-2 text-xs text-[#77746E]">
        <span>{detail}</span>
      </div>
    </div>
  );
}
