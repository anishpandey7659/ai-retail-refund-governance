"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { type Order, type RefundRequest } from "@/types";
import { formatDate, formatMoney } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { OrderDetails } from "@/components/orders/OrderDetails";
import { RefundDetails } from "@/components/refunds/RefundDetails";
import { useAppData } from "@/context/app-context";
import { ArrowUpRight, Eye } from "lucide-react";

interface RecentActivityProps {
  recentOrders: Order[];
  recentRefunds: RefundRequest[];
}

export function RecentActivity({
  recentOrders,
  recentRefunds,
}: RecentActivityProps) {
  const { getRefundByOrderItemId } = useAppData();
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [selectedRefund, setSelectedRefund] = useState<RefundRequest | null>(
    null,
  );

  return (
    <>
      <div className="grid gap-6 xl:grid-cols-[1.7fr_1fr]">
        <section className="rounded-2xl border border-[#E8E6E1] bg-white p-5 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
          <div className="mb-5 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-[#252525]">
                Recent Orders
              </h2>
              <p className="text-xs text-[#77746E]">
                Latest purchases from your account
              </p>
            </div>
            <Link
              href="/orders"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#777D65] hover:text-[#5E644E]"
            >
              View all orders <ArrowUpRight size={14} />
            </Link>
          </div>

          <div className="overflow-hidden rounded-xl border border-[#EEEAE4]">
            <div className="grid grid-cols-[1.1fr_1.4fr_0.9fr_0.8fr_0.9fr_0.9fr] gap-3 bg-[#F8F7F4] px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#77746E]">
              <span>Order</span>
              <span>Product</span>
              <span>Date</span>
              <span>Amount</span>
              <span>Status</span>
              <span className="text-right">Action</span>
            </div>
            <div className="divide-y divide-[#F0ECE7]">
              {recentOrders.length === 0 ? (
                <p className="px-4 py-8 text-center text-xs text-[#77746E]">
                  No orders returned by the API.
                </p>
              ) : (
                recentOrders.map((order) => (
                  <div
                    key={order.orderItemId}
                    className="grid grid-cols-[1.1fr_1.4fr_0.9fr_0.8fr_0.9fr_0.9fr] items-center gap-3 px-4 py-3 text-xs hover:bg-[#FAF9F7]"
                  >
                    <span className="truncate font-semibold text-[#252525]">
                      {order.id}
                    </span>
                    <div className="flex min-w-0 items-center gap-2.5">
                      <div className="relative h-7 w-7 shrink-0 overflow-hidden rounded-lg border border-[#E8E6E1] bg-white">
                        {order.product.image ? (
                          <Image
                            src={order.product.image}
                            alt={order.product.name}
                            fill
                            className="object-cover"
                            sizes="28px"
                            unoptimized
                          />
                        ) : (
                          <div
                            className={`flex h-full w-full items-center justify-center text-[9px] font-bold ${order.product.tone}`}
                          >
                            {order.product.name.slice(0, 2).toUpperCase()}
                          </div>
                        )}
                      </div>
                      <span className="truncate font-medium text-[#252525]">
                        {order.product.name}
                      </span>
                    </div>
                    <span className="text-[#67635F]">
                      {formatDate(order.orderDate)}
                    </span>
                    <span className="font-semibold tabular-nums text-[#252525]">
                      {formatMoney(order.totalPrice)}
                    </span>
                    <Badge status={order.orderStatus} size="sm" />
                    <div className="text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedOrder(order)}
                      >
                        <Eye size={12} />
                        <span className="hidden sm:inline">Details</span>
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-[#E8E6E1] bg-white p-5 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
          <div className="mb-5 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-[#252525]">
                Recent Returns
              </h2>
              <p className="text-xs text-[#77746E]">
                Status and decisions from the API
              </p>
            </div>
            <Link
              href="/refunds"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#777D65] hover:text-[#5E644E]"
            >
              All returns <ArrowUpRight size={14} />
            </Link>
          </div>
          <div className="space-y-3">
            {recentRefunds.length === 0 ? (
              <p className="py-8 text-center text-xs text-[#77746E]">
                No return requests returned by the API.
              </p>
            ) : (
              recentRefunds.map((request) => (
                <button
                  type="button"
                  key={request.id}
                  onClick={() => setSelectedRefund(request)}
                  className="block w-full rounded-xl border border-[#F0ECE7] bg-[#FAF9F7] p-3.5 text-left transition hover:border-[#DED9D0] hover:bg-white"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-[11px] font-semibold uppercase tracking-[0.1em] text-[#77746E]">
                        {request.id}
                      </p>
                      <h3 className="mt-1 truncate text-xs font-semibold text-[#252525]">
                        {request.product.name}
                      </h3>
                    </div>
                    <Badge status={request.reviewStatus} size="sm" />
                  </div>
                  <div className="mt-3 flex items-center justify-between border-t border-[#F2EFEA] pt-2.5 text-xs">
                    <span className="font-semibold tabular-nums text-[#252525]">
                      {formatMoney(request.requestedAmount)}
                    </span>
                    <span className="text-[11px] text-[#8C8880]">
                      {formatDate(request.submissionDate)}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </section>
      </div>

      <OrderDetails
        isOpen={Boolean(selectedOrder)}
        order={selectedOrder}
        refundRequest={
          selectedOrder
            ? getRefundByOrderItemId(selectedOrder.orderItemId)
            : undefined
        }
        onClose={() => setSelectedOrder(null)}
      />
      <RefundDetails
        isOpen={Boolean(selectedRefund)}
        request={selectedRefund}
        onClose={() => setSelectedRefund(null)}
      />
    </>
  );
}
