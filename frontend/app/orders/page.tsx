"use client";

import React, { useMemo, useState } from "react";
import { AlertCircle, Search } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { OrdersTable } from "@/components/orders/OrdersTable";
import { OrderDetails } from "@/components/orders/OrderDetails";
import { RefundRequestDialog } from "@/components/orders/RefundRequestDialog";
import { useAppData } from "@/context/app-context";
import { type Order } from "@/types";

const refundStatusOptions = [
  "All",
  "Not Requested",
  "Pending Review",
  "Approved",
  "Denied",
  "Refunded",
];

export default function OrdersPage() {
  const {
    orders,
    submitRefundRequest,
    getRefundByOrderItemId,
    accountError,
    isAuthReady,
    user,
  } = useAppData();
  const canAccessOrders = user?.roles.includes("customer") ?? false;

  const [searchTerm, setSearchTerm] = useState("");
  const [orderStatusFilter, setOrderStatusFilter] = useState("All");
  const [refundStatusFilter, setRefundStatusFilter] = useState("All");

  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [refundOrder, setRefundOrder] = useState<Order | null>(null);

  const orderStatusOptions = useMemo(
    () => ["All", ...new Set(orders.map((order) => order.orderStatus))],
    [orders],
  );

  const filteredOrders = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    return orders.filter((order) => {
      const matchesSearch =
        query.length === 0 ||
        order.id.toLowerCase().includes(query) ||
        order.product.name.toLowerCase().includes(query) ||
        order.customer.name.toLowerCase().includes(query);

      const matchesOrderStatus =
        orderStatusFilter === "All" || order.orderStatus === orderStatusFilter;

      const matchesRefundStatus =
        refundStatusFilter === "All" || order.refundStatus === refundStatusFilter;

      return matchesSearch && matchesOrderStatus && matchesRefundStatus;
    });
  }, [orders, orderStatusFilter, refundStatusFilter, searchTerm]);

  if (!isAuthReady) return null;

  if (!canAccessOrders) {
    return (
      <main className="flex min-h-screen items-center justify-center px-4">
        <section className="max-w-md rounded-2xl border border-[#E8E6E1] bg-white p-8 text-center shadow-sm">
          <AlertCircle className="mx-auto text-[#8A5147]" size={28} />
          <h1 className="mt-4 text-xl font-semibold">Access restricted</h1>
          <p className="mt-2 text-sm text-[#77746E]">
            Orders are available to customer accounts only.
          </p>
        </section>
      </main>
    );
  }

  return (
    <AppShell
      title="Orders"
      description="Review your purchased items and submit return requests for eligible order items."
    >
      <div className="space-y-6">
        {accountError && (
          <div
            role="alert"
            className="rounded-xl border border-[#E1B8B0] bg-[#FBEBE8] p-3 text-sm text-[#783D31]"
          >
            Could not load the latest account data: {accountError}
          </div>
        )}
        {/* Search & Filters Bar */}
        <div className="rounded-2xl border border-[#E8E6E1] bg-white p-4 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
          <div className="flex flex-col gap-3.5 md:flex-row md:items-center md:justify-between">
            {/* Search Input */}
            <div className="relative w-full md:max-w-md">
              <Search
                size={16}
                className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[#8C8880]"
              />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by order ID, product, or account..."
                className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] py-2.5 pl-10 pr-3.5 text-xs text-[#252525] placeholder:text-[#8C8880] focus:border-[#777D65] focus:bg-white focus:outline-none transition-colors"
              />
            </div>

            {/* Filter Dropdowns */}
            <div className="flex flex-wrap items-center gap-2.5">
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#77746E]">
                  Status:
                </span>
                <select
                  value={orderStatusFilter}
                  onChange={(e) => setOrderStatusFilter(e.target.value)}
                  className="rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3 py-2 text-xs text-[#252525] focus:border-[#777D65] focus:bg-white focus:outline-none transition-colors cursor-pointer"
                >
                  {orderStatusOptions.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt === "All"
                        ? "All Orders"
                        : opt.charAt(0).toUpperCase() + opt.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#77746E]">
                  Returns:
                </span>
                <select
                  value={refundStatusFilter}
                  onChange={(e) => setRefundStatusFilter(e.target.value)}
                  className="rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3 py-2 text-xs text-[#252525] focus:border-[#777D65] focus:bg-white focus:outline-none transition-colors cursor-pointer"
                >
                  {refundStatusOptions.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt === "All" ? "All Returns" : opt}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Orders Table */}
        <OrdersTable
          orders={filteredOrders}
          onViewDetails={(order) => setSelectedOrder(order)}
          onRequestRefund={(order) => setRefundOrder(order)}
        />
      </div>

      {/* Order Details Modal */}
      <OrderDetails
        order={selectedOrder}
        refundRequest={
          selectedOrder
            ? getRefundByOrderItemId(selectedOrder.orderItemId)
            : undefined
        }
        isOpen={Boolean(selectedOrder)}
        onClose={() => setSelectedOrder(null)}
        onRequestRefund={(order) => setRefundOrder(order)}
      />

      {/* Refund Request Submission Modal */}
      <RefundRequestDialog
        order={refundOrder}
        isOpen={Boolean(refundOrder)}
        onClose={() => setRefundOrder(null)}
        onSubmit={submitRefundRequest}
      />
    </AppShell>
  );
}
