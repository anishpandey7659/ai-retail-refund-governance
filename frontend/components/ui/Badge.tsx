import React from "react";
import { cn, statusStyleMap } from "@/lib/utils";

interface BadgeProps {
  status: string;
  className?: string;
  size?: "sm" | "md";
}

export function Badge({ status, className, size = "sm" }: BadgeProps) {
  const style = statusStyleMap[status] || {
    bg: "bg-[#F3F1ED]",
    text: "text-[#6B6661]",
    border: "border-[#E2DED7]",
    label: status,
  };

  const sizeClasses =
    size === "sm"
      ? "px-2.5 py-0.5 text-[11px] font-medium"
      : "px-3 py-1 text-xs font-medium";

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border tracking-wide transition-colors",
        style.bg,
        style.text,
        style.border,
        sizeClasses,
        className,
      )}
    >
      <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current opacity-70" />
      {style.label}
    </span>
  );
}
