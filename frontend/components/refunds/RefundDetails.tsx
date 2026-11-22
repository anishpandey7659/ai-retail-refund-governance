"use client";

import React from "react";
import Image from "next/image";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { type RefundRequest } from "@/types";
import { formatDate, formatMoney } from "@/lib/utils";

interface RefundDetailsProps {
  request: RefundRequest | null;
  isOpen: boolean;
  onClose: () => void;
}

export function RefundDetails({
  request,
  isOpen,
  onClose,
}: RefundDetailsProps) {
  if (!request) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      subtitle="Return Request"
      title={`Request ${request.id}`}
      maxWidth="2xl"
      footer={
        <div className="flex w-full items-center justify-between">
          <div className="text-xs text-[#77746E]">
            Submitted {formatDate(request.submissionDate)}
          </div>
          <Button variant="outline" size="md" onClick={onClose}>
            Close
          </Button>
        </div>
      }
    >
      <div className="space-y-5">
        <div className="flex items-center justify-between rounded-2xl border border-[#E8E6E1] bg-[#F8F7F4] p-4">
          <div>
            <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#77746E]">
              API Status
            </span>
            <div className="mt-1">
              <Badge status={request.reviewStatus} size="md" />
            </div>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#77746E]">
              Return Amount
            </span>
            <div className="mt-1 text-2xl font-bold text-[#252525] tabular-nums">
              {formatMoney(request.requestedAmount)}
            </div>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-[#E9E5DF] p-4">
            <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#77746E]">
              Account
            </span>
            <div className="mt-2.5 space-y-1 text-xs">
              <p className="font-semibold text-[#252525]">
                {request.customer.name}
              </p>
              <p className="text-[#67635F]">{request.customer.email}</p>
            </div>
          </div>
          <div className="rounded-2xl border border-[#E9E5DF] p-4">
            <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#77746E]">
              Order Information
            </span>
            <div className="mt-2.5 space-y-1 text-xs">
              <div className="flex justify-between gap-3">
                <span className="text-[#77746E]">Order ID:</span>
                <span className="font-semibold text-[#252525]">
                  {request.orderId}
                </span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-[#77746E]">Purchase date:</span>
                <span className="text-[#252525]">
                  {formatDate(request.orderDate)}
                </span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-[#77746E]">Item quantity:</span>
                <span className="text-[#252525]">{request.quantity}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-[#E9E5DF] bg-[#F8F7F4] p-3.5">
          <div className="flex items-center gap-3">
            <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-xl border border-[#E0DCD4] bg-white">
              {request.product.image ? (
                <Image
                  src={request.product.image}
                  alt={request.product.name}
                  fill
                  className="object-cover"
                  sizes="48px"
                  unoptimized
                />
              ) : (
                <div
                  className={`flex h-full w-full items-center justify-center text-xs font-bold ${request.product.tone}`}
                >
                  {request.product.name.slice(0, 2).toUpperCase()}
                </div>
              )}
            </div>
            <div>
              <p className="text-xs font-semibold text-[#252525]">
                {request.product.name}
              </p>
              <p className="text-[11px] text-[#77746E]">
                {request.product.category}
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-3 rounded-2xl border border-[#E9E5DF] p-4">
          <div className="flex items-center justify-between gap-3">
            <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#77746E]">
              Reason
            </span>
            <span className="text-xs font-medium text-[#252525]">
              {request.reason}
            </span>
          </div>
          <div>
            <span className="mb-1 block text-[10px] font-semibold uppercase tracking-[0.14em] text-[#77746E]">
              Customer Explanation
            </span>
            <div className="rounded-xl border border-[#F0ECE7] bg-[#FAF9F7] p-3 text-xs leading-relaxed text-[#443F3A]">
              {request.description || "No additional explanation provided."}
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <p className="text-xs text-[#555048]">
              <span className="font-semibold text-[#252525]">
                AI proposed decision:{" "}
              </span>
              {request.aiProposedDecision || "Not available"}
            </p>
            <p className="text-xs text-[#555048]">
              <span className="font-semibold text-[#252525]">
                Final decision:{" "}
              </span>
              {request.finalDecision || "Not available"}
            </p>
          </div>
          {request.photoUrls.length > 0 && (
            <div>
              <span className="mb-2 block text-[10px] font-semibold uppercase tracking-[0.14em] text-[#77746E]">
                Evidence
              </span>
              <div className="flex flex-wrap gap-2">
                {request.photoUrls.map((url, index) => (
                  <a
                    key={url}
                    href={url}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-lg border border-[#E8E6E1] bg-white px-3 py-2 text-xs font-medium text-[#555048] hover:text-[#252525]"
                  >
                    View photo {index + 1}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}
