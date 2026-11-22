"use client";

import React from "react";
import Image from "next/image";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { type Order, type RefundRequest } from "@/types";
import { formatDate, formatMoney } from "@/lib/utils";
import { ShoppingBag } from "lucide-react";

interface OrderDetailsProps {
  order: Order | null;
  refundRequest?: RefundRequest;
  isOpen: boolean;
  onClose: () => void;
  onRequestRefund?: (order: Order) => void;
}

export function OrderDetails({
  order,
  refundRequest,
  isOpen,
  onClose,
  onRequestRefund,
}: OrderDetailsProps) {
  if (!order) return null;

  const canRequestRefund =
    order.refundStatus === "Not Requested" || order.refundStatus === "Denied";

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      subtitle="Order Overview"
      title={order.id}
      maxWidth="xl"
      footer={
        <div className="flex items-center justify-between w-full">
          <div className="text-xs text-[#77746E]">
            Purchased on {formatDate(order.orderDate)}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="md" onClick={onClose}>
              Close
            </Button>
            {canRequestRefund && onRequestRefund && (
              <Button
                variant="primary"
                size="md"
                onClick={() => {
                  onClose();
                  onRequestRefund(order);
                }}
              >
                <ShoppingBag size={14} /> Request Return
              </Button>
            )}
          </div>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Product Card */}
        <div className="rounded-2xl border border-[#E9E5DF] bg-[#F8F7F4] p-4">
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-[#77746E]">
            Purchased Item
          </div>
          <div className="flex items-center gap-4">
            <div className="relative h-16 w-16 overflow-hidden rounded-xl border border-[#E0DCD4] bg-white shrink-0">
              {order.product.image ? (
                <Image
                  src={order.product.image}
                  alt={order.product.name}
                  fill
                  className="object-cover"
                  sizes="64px"
                  unoptimized
                />
              ) : (
                <div
                  className={`flex h-full w-full items-center justify-center font-bold text-sm ${order.product.tone}`}
                >
                  {order.product.name.slice(0, 2).toUpperCase()}
                </div>
              )}
            </div>
            <div className="min-w-0 flex-1">
              <h4 className="text-base font-semibold text-[#252525]">
                {order.product.name}
              </h4>
              <p className="text-xs text-[#77746E] mt-0.5">
                SKU: {order.product.id} • Category: {order.product.category}
              </p>
              <div className="mt-2 text-xs font-medium text-[#252525]">
                {formatMoney(order.unitPrice)} × {order.quantity} unit
                {order.quantity > 1 ? "s" : ""}
              </div>
            </div>
          </div>
        </div>

        {/* Customer & Fulfillment Info */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-[#E9E5DF] p-4">
            <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#77746E]">
              Customer Details
            </div>
            <div className="mt-2.5 space-y-1 text-xs">
              <div className="font-semibold text-[#252525]">
                {order.customer.name}
              </div>
              <div className="text-[#6E6965]">{order.customer.email}</div>
              <div className="text-[11px] text-[#8C8880]">
                Customer ID: {order.customer.id}
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-[#E9E5DF] p-4">
            <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#77746E]">
              Order Financials
            </div>
            <div className="mt-2.5 space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-[#77746E]">Total Amount:</span>
                <span className="font-bold text-[#252525] tabular-nums">
                  {formatMoney(order.orderTotal)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#77746E]">Payment card:</span>
                <span className="font-medium text-[#252525]">
                  ending in {order.paymentLast4}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Return Status Context */}
        <div className="rounded-2xl border border-[#E9E5DF] bg-white p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#77746E]">
              Return Request Status
            </span>
            <Badge status={order.refundStatus} />
          </div>

          {refundRequest ? (
            <div className="rounded-xl border border-[#EFECE6] bg-[#FAF9F7] p-3.5 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-[#252525]">
                  Return ID: {refundRequest.id}
                </span>
                <span className="font-medium text-[#777D65] tabular-nums">
                  {formatMoney(refundRequest.requestedAmount)} return amount
                </span>
              </div>
              <div className="text-[#555048]">
                <span className="font-medium text-[#252525]">Reason: </span>
                {refundRequest.reason}
              </div>
              <div className="text-[#67635F] italic bg-white p-2.5 rounded-lg border border-[#EAE6DF]">
                &ldquo;{refundRequest.description}&rdquo;
              </div>

            </div>
          ) : (
            <p className="text-xs text-[#77746E]">
              No return request has been submitted for this item.
            </p>
          )}
        </div>
      </div>
    </Modal>
  );
}
