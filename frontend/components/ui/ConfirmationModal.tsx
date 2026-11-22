"use client";

import React from "react";
import { Modal } from "./Modal";
import { Button } from "./Button";
import { AlertCircle, CheckCircle2 } from "lucide-react";

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "primary" | "danger";
  isLoading?: boolean;
}

export function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "primary",
  isLoading = false,
}: ConfirmationModalProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="sm"
      footer={
        <>
          <Button variant="outline" size="md" onClick={onClose} disabled={isLoading}>
            {cancelLabel}
          </Button>
          <Button
            variant={variant === "danger" ? "danger" : "primary"}
            size="md"
            onClick={onConfirm}
            isLoading={isLoading}
          >
            {confirmLabel}
          </Button>
        </>
      }
    >
      <div className="flex gap-4 py-2">
        <div
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ${
            variant === "danger"
              ? "bg-[#EFD6D1] text-[#783D31]"
              : "bg-[#DFEAE0] text-[#2D4E35]"
          }`}
        >
          {variant === "danger" ? (
            <AlertCircle size={20} />
          ) : (
            <CheckCircle2 size={20} />
          )}
        </div>
        <div>
          <h4 className="text-base font-semibold text-[#252525]">{title}</h4>
          <p className="mt-1.5 text-sm leading-relaxed text-[#77746E]">
            {description}
          </p>
        </div>
      </div>
    </Modal>
  );
}
