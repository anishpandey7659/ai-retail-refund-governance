"use client";

import React, { useMemo, useState } from "react";
import { AlertCircle, Search } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { RefundsTable } from "@/components/refunds/RefundsTable";
import { RefundDetails } from "@/components/refunds/RefundDetails";
import { useAppData } from "@/context/app-context";
import { type RefundRequest } from "@/types";

export default function RefundsPage() {
  const { refundRequests, accountError, isAuthReady, user } = useAppData();
  const canAccessReturns = user?.roles.includes("customer") ?? false;
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [selectedRequest, setSelectedRequest] = useState<RefundRequest | null>(
    null,
  );

  const statusOptions = useMemo(
    () => [
      "All",
      ...new Set(refundRequests.map((request) => request.reviewStatus)),
    ],
    [refundRequests],
  );
  const filteredRequests = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();
    return refundRequests.filter((request) => {
      const matchesSearch =
        !query ||
        request.id.toLowerCase().includes(query) ||
        request.orderId.toLowerCase().includes(query) ||
        request.product.name.toLowerCase().includes(query) ||
        request.reason.toLowerCase().includes(query);
      return (
        matchesSearch &&
        (statusFilter === "All" || request.reviewStatus === statusFilter)
      );
    });
  }, [refundRequests, searchTerm, statusFilter]);

  const stats = [
    { label: "Total Returns", value: refundRequests.length },
    {
      label: "Pending",
      value: refundRequests.filter((r) => r.reviewStatus === "Pending Review")
        .length,
    },
    {
      label: "Approved",
      value: refundRequests.filter((r) => r.reviewStatus === "Approved").length,
    },
    {
      label: "Denied",
      value: refundRequests.filter((r) => r.reviewStatus === "Denied").length,
    },
  ];

  if (!isAuthReady) return null;

  if (!canAccessReturns) {
    return (
      <main className="flex min-h-screen items-center justify-center px-4">
        <section className="max-w-md rounded-2xl border border-[#E8E6E1] bg-white p-8 text-center shadow-sm">
          <AlertCircle className="mx-auto text-[#8A5147]" size={28} />
          <h1 className="mt-4 text-xl font-semibold">Access restricted</h1>
          <p className="mt-2 text-sm text-[#77746E]">
            My Returns are available to customer accounts only.
          </p>
        </section>
      </main>
    );
  }

  return (
    <AppShell
      title="My Returns"
      description="Return requests and AI decisions loaded from your account in the FastAPI service."
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

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-2xl border border-[#E8E6E1] bg-white p-5 shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
            >
              <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#77746E]">
                {stat.label}
              </span>
              <div className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[#252525] tabular-nums">
                {stat.value}
              </div>
            </div>
          ))}
        </section>

        <div className="rounded-2xl border border-[#E8E6E1] bg-white p-4 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
          <div className="flex flex-col gap-3.5 md:flex-row md:items-center md:justify-between">
            <div className="relative w-full md:max-w-md">
              <Search
                size={16}
                className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[#8C8880]"
              />
              <input
                type="text"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search by request, order, or product..."
                className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] py-2.5 pl-10 pr-3.5 text-xs text-[#252525] placeholder:text-[#8C8880] focus:border-[#777D65] focus:bg-white focus:outline-none"
              />
            </div>
            <div className="flex items-center gap-2">
              <label
                htmlFor="return-status"
                className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#77746E]"
              >
                Status:
              </label>
              <select
                id="return-status"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3 py-2 text-xs text-[#252525] focus:border-[#777D65] focus:outline-none"
              >
                {statusOptions.map((option) => (
                  <option key={option} value={option}>
                    {option === "All" ? "All statuses" : option}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <RefundsTable
          refundRequests={filteredRequests}
          onViewDetails={setSelectedRequest}
        />
      </div>

      <RefundDetails
        request={selectedRequest}
        isOpen={Boolean(selectedRequest)}
        onClose={() => setSelectedRequest(null)}
      />
    </AppShell>
  );
}
