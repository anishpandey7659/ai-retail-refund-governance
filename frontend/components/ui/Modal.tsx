"use client";

import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "3xl";
}

export function Modal({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footer,
  maxWidth = "lg",
}: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    } else {
      document.body.style.overflow = "";
    }

    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const maxWidthClasses = {
    sm: "max-w-md",
    md: "max-w-lg",
    lg: "max-w-xl",
    xl: "max-w-2xl",
    "2xl": "max-w-3xl",
    "3xl": "max-w-4xl",
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) {
      onClose();
    }
  };

  return (
    <div
      ref={overlayRef}
      onClick={handleBackdropClick}
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#1D1B1A]/40 p-4 backdrop-blur-[2px] transition-opacity"
      role="dialog"
      aria-modal="true"
    >
      <div
        className={cn(
          "w-full overflow-hidden rounded-3xl border border-[#E8E6E1] bg-white shadow-[0_24px_50px_rgba(30,27,24,0.14)] animate-in fade-in-0 zoom-in-95 duration-200 max-h-[90vh] flex flex-col",
          maxWidthClasses[maxWidth],
        )}
      >
        {/* Header */}
        {(title || subtitle) && (
          <div className="flex items-start justify-between border-b border-[#F0ECE7] px-6 py-5">
            <div>
              {subtitle && (
                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#77746E]">
                  {subtitle}
                </p>
              )}
              {title && (
                <h3 className="mt-1 text-xl font-semibold tracking-[-0.03em] text-[#252525]">
                  {title}
                </h3>
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="flex h-9 w-9 items-center justify-center rounded-full border border-[#E8E6E1] bg-[#F8F7F4] text-[#67635F] transition hover:bg-[#F1F0EC] hover:text-[#252525]"
              aria-label="Close dialog"
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-5">{children}</div>

        {/* Footer */}
        {footer && (
          <div className="flex items-center justify-end gap-3 border-t border-[#F0ECE7] bg-[#FBFBFA] px-6 py-4">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
