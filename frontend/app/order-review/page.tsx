"use client";

import React, { useMemo, useState } from "react";
import { AlertCircle, Search } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ConfirmationModal } from "@/components/ui/ConfirmationModal";
import { DataTable } from "@/components/ui/DataTable";
import { useAppData } from "@/context/app-context";
import type { BackendReviewOrder } from "@/lib/retail-api";
import { formatDate, formatMoney } from "@/lib/utils";

function orderStatusLabel(status: string): string {
  if (status.toLowerCase() === "placed") return "Placed";
  return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
}

export default function OrderReviewPage() {
  const {
    accountError,
    isAuthReady,
    markOrderDelivered,
    reviewOrders,
    user,
  } = useAppData();
  const [search, setSearch] = useState("");
  const [selectedOrder, setSelectedOrder] = useState<BackendReviewOrder | null>(
    null,
  );
  const [isUpdating, setIsUpdating] = useState(false);

  const canReview = Boolean(
    user?.roles.some((role) => role === "admin" || role === "reviewer"),
  );
  const filteredOrders = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return reviewOrders;
    return reviewOrders.filter((order) =>
      [
        order.id,
        order.customer_name,
        order.customer_email,
        ...order.items.map((item) => item.name),
      ].some((value) => value.toLowerCase().includes(query)),
    );
  }, [reviewOrders, search]);

  const confirmDelivery = async () => {
    if (!selectedOrder) return;
    setIsUpdating(true);
    const result = await markOrderDelivered(selectedOrder.id);
    setIsUpdating(false);
    if (result.success) setSelectedOrder(null);
  };

  if (!isAuthReady) return null;

  if (!canReview) {
    return (
      <main className="flex min-h-screen items-center justify-center px-4">
        <section className="max-w-md rounded-2xl border border-[#E8E6E1] bg-white p-8 text-center shadow-sm">
          <AlertCircle className="mx-auto text-[#8A5147]" size={28} />
          <h1 className="mt-4 text-xl font-semibold">Access restricted</h1>
          <p className="mt-2 text-sm text-[#77746E]">
            This page is available to administrators and reviewers only.
          </p>
        </section>
      </main>
    );
  }

  return (
    <AppShell
      title="Order Review"
      description="Review pending orders and mark fulfilled orders as delivered."
    >
      <div className="space-y-6">
        {accountError && (
          <div
            role="alert"
            className="rounded-xl border border-[#E1B8B0] bg-[#FBEBE8] p-3 text-sm text-[#783D31]"
          >
            Could not load orders: {accountError}
          </div>
        )}

        <section className="rounded-2xl border border-[#E8E6E1] bg-white p-5 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
          <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#77746E]">
            Pending orders
          </span>
          <div className="mt-2 text-3xl font-semibold tracking-[-0.04em] tabular-nums">
            {reviewOrders.length}
          </div>
        </section>

        <div className="rounded-2xl border border-[#E8E6E1] bg-white p-4">
          <div className="relative w-full md:max-w-md">
            <Search
              size={16}
              className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[#8C8880]"
            />
            <input
              aria-label="Search pending orders"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search by order, customer, or product..."
              className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] py-2.5 pl-10 pr-3.5 text-xs focus:border-[#777D65] focus:bg-white focus:outline-none"
            />
          </div>
        </div>

        <DataTable
          headers={[
            "Order",
            "Customer",
            "Ship to",
            "Items",
            "Placed",
            "Total",
            "Status",
            "Action",
          ]}
          isEmpty={filteredOrders.length === 0}
          emptyTitle={accountError ? "Orders unavailable" : "No pending orders"}
          emptyDescription={
            accountError
              ? "Check the API connection and try again."
              : search
                ? "No pending orders match your search."
                : "All orders have been reviewed."
          }
        >
          {filteredOrders.map((order) => (
            <tr key={order.id} className="hover:bg-[#FCFBF9]">
              <td className="whitespace-nowrap px-4 py-4 font-medium sm:px-5">
                {order.id}
              </td>
              <td className="px-4 py-4 sm:px-5">
                <p className="font-medium text-[#252525]">{order.customer_name}</p>
                <p className="mt-0.5 text-xs text-[#77746E]">
                  {order.customer_email}
                </p>
              </td>
              <td className="min-w-48 px-4 py-4 text-xs sm:px-5">
                {order.shipping_address}
              </td>
              <td className="min-w-48 px-4 py-4 sm:px-5">
                <ul className="space-y-1 text-xs">
                  {order.items.map((item) => (
                    <li key={item.id}>
                      {item.name} <span className="text-[#77746E]">× {item.qty}</span>
                    </li>
                  ))}
                </ul>
              </td>
              <td className="whitespace-nowrap px-4 py-4 sm:px-5">
                {formatDate(order.placed_at)}
              </td>
              <td className="whitespace-nowrap px-4 py-4 tabular-nums sm:px-5">
                {formatMoney(Number(order.total))}
              </td>
              <td className="whitespace-nowrap px-4 py-4 sm:px-5">
                <Badge status={orderStatusLabel(order.status)} />
              </td>
              <td className="whitespace-nowrap px-4 py-4 text-right sm:px-5">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setSelectedOrder(order)}
                >
                  Mark Delivered
                </Button>
              </td>
            </tr>
          ))}
        </DataTable>
      </div>

      <ConfirmationModal
        isOpen={Boolean(selectedOrder)}
        onClose={() => setSelectedOrder(null)}
        onConfirm={() => void confirmDelivery()}
        title="Mark order as delivered?"
        description={
          selectedOrder
            ? `Order ${selectedOrder.id} will be marked as delivered.`
            : ""
        }
        confirmLabel="Mark Delivered"
        isLoading={isUpdating}
      />
    </AppShell>
  );
}
