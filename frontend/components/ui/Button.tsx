import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      className,
      variant = "secondary",
      size = "md",
      disabled,
      isLoading,
      ...props
    },
    ref,
  ) => {
    const baseClasses =
      "inline-flex items-center justify-center font-medium transition-all duration-150 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#777D65]/30 disabled:cursor-not-allowed disabled:opacity-50 select-none cursor-pointer";

    const variantClasses = {
      primary:
        "bg-[#777D65] hover:bg-[#686E56] text-white shadow-xs active:scale-[0.99]",
      secondary:
        "bg-[#F1F0EC] hover:bg-[#EAE8E2] text-[#252525] border border-[#E8E6E1] active:scale-[0.99]",
      outline:
        "bg-white hover:bg-[#F8F7F4] text-[#252525] border border-[#E8E6E1] hover:border-[#D6D3CB] active:scale-[0.99]",
      danger:
        "bg-[#EFD6D1] hover:bg-[#E7C6C0] text-[#783D31] border border-[#E1B8B0] active:scale-[0.99]",
      ghost:
        "bg-transparent hover:bg-[#F1F0EC] text-[#67635F] hover:text-[#252525]",
    };

    const sizeClasses = {
      sm: "text-xs px-3 py-1.5 gap-1.5",
      md: "text-xs font-medium px-3.5 py-2 gap-2",
      lg: "text-sm px-4 py-2.5 gap-2.5",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          baseClasses,
          variantClasses[variant],
          sizeClasses[size],
          className,
        )}
        {...props}
      >
        {isLoading && (
          <svg
            className="animate-spin -ml-0.5 h-3.5 w-3.5 text-current opacity-70"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
            />
          </svg>
        )}
        {children}
      </button>
    );
  },
);

Button.displayName = "Button";
