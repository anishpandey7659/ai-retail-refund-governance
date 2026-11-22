"use client";

import React, { useState } from "react";
import Image from "next/image";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { type Order } from "@/types";
import { AlertCircle } from "lucide-react";

interface RefundRequestDialogProps {
  order: Order | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (input: {
    orderItemId: string;
    reasonCode: string;
    description: string;
    photo: File;
  }) => Promise<{ success: boolean; message: string }>;
}

const returnReasons = [
  { code: "damaged", label: "Damaged" },
  { code: "not_as_described", label: "Not as described" },
  { code: "wrong_item", label: "Wrong item" },
  { code: "no_longer_needed", label: "No longer needed" },
  { code: "defective", label: "Defective" },
  { code: "arrived_late", label: "Arrived late" },
  { code: "quality", label: "Quality issue" },
];

export function RefundRequestDialog({
  order,
  isOpen,
  onClose,
  onSubmit,
}: RefundRequestDialogProps) {
  if (!isOpen || !order) return null;

  return (
    <RefundRequestDialogInner
      key={`${order.id}:${order.orderItemId}`}
      order={order}
      onClose={onClose}
      onSubmit={onSubmit}
    />
  );
}

function RefundRequestDialogInner({
  order,
  onClose,
  onSubmit,
}: {
  order: Order;
  onClose: () => void;
  onSubmit: (input: {
    orderItemId: string;
    reasonCode: string;
    description: string;
    photo: File;
  }) => Promise<{ success: boolean; message: string }>;
}) {
  const [reasonCode, setReasonCode] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [error, setError] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleSubmit = async () => {
    setError("");

    if (!reasonCode) {
      setError("Please select a reason for the return.");
      return;
    }

    if (!description.trim()) {
      setError("Please enter a short explanation describing the issue.");
      return;
    }

    if (!photo) {
      setError("Please attach a supporting photo.");
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await onSubmit({
        orderItemId: order.orderItemId,
        reasonCode,
        description,
        photo,
      });
      if (result.success) {
        onClose();
      } else {
        setError(result.message);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      subtitle="Customer Action"
      title="Request a Return"
      maxWidth="md"
      footer={
        <>
          <Button
            variant="outline"
            size="md"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={() => void handleSubmit()}
            isLoading={isSubmitting}
          >
            Submit Return Request
          </Button>
        </>
      }
    >
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void handleSubmit();
        }}
        className="space-y-4"
      >
        {/* Order Summary */}
        <div className="rounded-2xl border border-[#E9E5DF] bg-[#F8F7F4] p-3.5">
          <div className="flex items-center gap-3">
            <div className="relative h-12 w-12 overflow-hidden rounded-xl border border-[#E0DCD4] bg-white shrink-0">
              {order.product.image ? (
                <Image
                  src={order.product.image}
                  alt={order.product.name}
                  fill
                  className="object-cover"
                  sizes="48px"
                  unoptimized
                />
              ) : (
                <div
                  className={`flex h-full w-full items-center justify-center font-bold text-xs ${order.product.tone}`}
                >
                  {order.product.name.slice(0, 2).toUpperCase()}
                </div>
              )}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[#252525] truncate">
                  {order.product.name}
                </span>
              </div>
              <p className="text-[11px] text-[#77746E] mt-0.5">
                Order ID: {order.id} • Qty: {order.quantity}
              </p>
            </div>
          </div>
        </div>

        {/* Reason Select */}
        <div>
          <label className="block text-xs font-semibold text-[#252525] mb-1.5">
            Return Reason <span className="text-[#A24838]">*</span>
          </label>
          <select
            value={reasonCode}
            onChange={(e) => setReasonCode(e.target.value)}
            className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3.5 py-2.5 text-xs text-[#252525] focus:border-[#777D65] focus:bg-white focus:outline-none transition-colors cursor-pointer"
          >
            <option value="">Select a reason</option>
            {returnReasons.map((reason) => (
              <option key={reason.code} value={reason.code}>
                {reason.label}
              </option>
            ))}
          </select>
        </div>

        {/* Description Textarea */}
        <div>
          <label className="block text-xs font-semibold text-[#252525] mb-1.5">
            Explanation / Details <span className="text-[#A24838]">*</span>
          </label>
          <textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Please explain why you are requesting a return and describe the issue..."
            className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3.5 py-2.5 text-xs text-[#252525] focus:border-[#777D65] focus:bg-white focus:outline-none transition-colors resize-none leading-relaxed"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-[#252525] mb-1.5">
            Evidence Photo <span className="text-[#A24838]">*</span>
          </label>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            required
            onChange={(event) => setPhoto(event.target.files?.[0] ?? null)}
            className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3.5 py-2.5 text-xs text-[#252525] file:mr-3 file:rounded-lg file:border-0 file:bg-white file:px-3 file:py-1.5 file:text-xs file:font-medium"
          />
          <p className="mt-1 text-[11px] text-[#77746E]">
            JPEG, PNG, or WebP. The API calculates the return amount from the order item.
          </p>
        </div>

        {/* Error banner */}
        {error && (
          <div className="flex items-start gap-2 rounded-xl border border-[#E1B8B0] bg-[#EFD6D1] p-3 text-xs text-[#783D31]">
            <AlertCircle size={15} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
      </form>
    </Modal>
  );
}
