"use client";

import React, { useMemo, useState } from "react";
import { AlertCircle, Search } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Badge } from "@/components/ui/Badge";
import { DataTable } from "@/components/ui/DataTable";
import { useAppData } from "@/context/app-context";
import type { BackendReturn } from "@/lib/retail-api";
import { formatDate, formatMoney } from "@/lib/utils";

function displayStatus(status: string): string {
  const labels: Record<string, string> = {
    pending: "Pending Review",
    in_review: "In Review",
    escalated: "Escalated",
    approved: "Approved",
    denied: "Denied",
    refunded: "Refunded",
  };
  return labels[status.toLowerCase()] ?? status;
}

export default function ReturnReviewPage() {
  const {
    accountError,
    getReturnDetails,
    isAuthReady,
    returnRecords,
    user,
  } = useAppData();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [selectedReturn, setSelectedReturn] = useState<BackendReturn | null>(
    null,
  );
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [detailsError, setDetailsError] = useState("");

  const canReview = Boolean(
    user?.roles.some((role) => role === "admin" || role === "reviewer"),
  );
  const statuses = useMemo(
    () => [
      "All",
      ...new Set(returnRecords.map((record) => displayStatus(record.status))),
    ],
    [returnRecords],
  );
  const filteredReturns = useMemo(() => {
    const query = search.trim().toLowerCase();
    return returnRecords.filter((record) => {
      const matchesSearch =
        !query ||
        record.id.toLowerCase().includes(query) ||
        record.order_id.toLowerCase().includes(query) ||
        record.reason_code.toLowerCase().includes(query) ||
        record.reason_text.toLowerCase().includes(query);
      return (
        matchesSearch &&
        (statusFilter === "All" ||
          displayStatus(record.status) === statusFilter)
      );
    });
  }, [returnRecords, search, statusFilter]);

  const openDetails = async (record: BackendReturn) => {
    setSelectedReturn(null);
    setDetailsError("");
    setIsLoadingDetails(true);
    try {
      setSelectedReturn(await getReturnDetails(record.id));
    } catch (error: unknown) {
      setDetailsError(
        error instanceof Error ? error.message : "Could not load return details.",
      );
    } finally {
      setIsLoadingDetails(false);
    }
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

  const pendingCount = returnRecords.filter((record) =>
    ["pending", "in_review", "escalated"].includes(record.status.toLowerCase()),
  ).length;

  return (
    <AppShell
      title="Return Review"
      description="Review submitted return requests and inspect their supporting details."
    >
      <div className="space-y-6">
        {accountError && (
          <div
            role="alert"
            className="rounded-xl border border-[#E1B8B0] bg-[#FBEBE8] p-3 text-sm text-[#783D31]"
          >
            Could not load return requests: {accountError}
          </div>
        )}

        <section className="grid gap-4 sm:grid-cols-3">
          {[
            { label: "All requests", value: returnRecords.length },
            { label: "Awaiting review", value: pendingCount },
            {
              label: "Resolved",
              value: returnRecords.length - pendingCount,
            },
          ].map((stat) => (
            <div
              key={stat.label}
              className="rounded-2xl border border-[#E8E6E1] bg-white p-5 shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
            >
              <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#77746E]">
                {stat.label}
              </span>
              <div className="mt-2 text-3xl font-semibold tracking-[-0.04em] tabular-nums">
                {stat.value}
              </div>
            </div>
          ))}
        </section>

        <div className="rounded-2xl border border-[#E8E6E1] bg-white p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="relative w-full md:max-w-md">
              <Search
                size={16}
                className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[#8C8880]"
              />
              <input
                aria-label="Search return requests"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search by return, order, or reason..."
                className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] py-2.5 pl-10 pr-3.5 text-xs focus:border-[#777D65] focus:bg-white focus:outline-none"
              />
            </div>
            <label className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.1em] text-[#77746E]">
              Status
              <select
                aria-label="Filter by return status"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3 py-2 text-xs font-normal normal-case tracking-normal text-[#252525]"
              >
                {statuses.map((status) => (
                  <option key={status} value={status}>
                    {status === "All" ? "All statuses" : status}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        <DataTable
          headers={[
            "Return",
            "Order",
            "Reason",
            "Status",
            "Amount",
            "Submitted",
            "Details",
          ]}
          isEmpty={filteredReturns.length === 0}
          emptyTitle={accountError ? "Returns unavailable" : "No returns found"}
          emptyDescription={
            accountError
              ? "Check the API connection and try again."
              : "No return requests match the current filters."
          }
        >
          {filteredReturns.map((record) => (
            <tr key={record.id} className="hover:bg-[#FCFBF9]">
              <td className="whitespace-nowrap px-4 py-4 font-medium sm:px-5">
                {record.id.slice(0, 8)}
              </td>
              <td className="whitespace-nowrap px-4 py-4 sm:px-5">
                {record.order_id}
              </td>
              <td className="px-4 py-4 sm:px-5">
                <span className="font-medium">
                  {record.reason_code.replaceAll("_", " ")}
                </span>
              </td>
              <td className="whitespace-nowrap px-4 py-4 sm:px-5">
                <Badge status={displayStatus(record.status)} />
              </td>
              <td className="whitespace-nowrap px-4 py-4 tabular-nums sm:px-5">
                {formatMoney(Number(record.amount))}
              </td>
              <td className="whitespace-nowrap px-4 py-4 sm:px-5">
                {formatDate(record.created_at)}
              </td>
              <td className="whitespace-nowrap px-4 py-4 text-right sm:px-5">
                <button
                  type="button"
                  aria-label={`View details for return ${record.id}`}
                  onClick={() => void openDetails(record)}
                  className="text-xs font-semibold text-[#62694F] hover:text-[#252525]"
                >
                  View
                </button>
              </td>
            </tr>
          ))}
        </DataTable>

        {(isLoadingDetails || detailsError || selectedReturn) && (
          <section
            aria-live="polite"
            className="rounded-2xl border border-[#E8E6E1] bg-white p-5"
          >
            {isLoadingDetails && (
              <p className="text-sm text-[#77746E]">Loading return details...</p>
            )}
            {detailsError && (
              <p role="alert" className="text-sm text-[#783D31]">
                Could not load return details: {detailsError}
              </p>
            )}
            {selectedReturn && (
              <div className="space-y-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#77746E]">
                      Return details
                    </p>
                    <h2 className="mt-1 break-all text-lg font-semibold">
                      {selectedReturn.id}
                    </h2>
                  </div>
                  <Badge status={displayStatus(selectedReturn.status)} />
                </div>
                <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {[
                    ["Order ID", selectedReturn.order_id],
                    ["Order item", selectedReturn.order_item_id],
                    [
                      "Reason",
                      selectedReturn.reason_code.replaceAll("_", " "),
                    ],
                    [
                      "Amount",
                      formatMoney(Number(selectedReturn.amount)),
                    ],
                    [
                      "AI proposed decision",
                      selectedReturn.ai_proposed_decision ?? "Not available",
                    ],
                    [
                      "Final decision",
                      selectedReturn.final_decision ?? "Not available",
                    ],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <dt className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[#77746E]">
                        {label}
                      </dt>
                      <dd className="mt-1 break-words text-sm text-[#252525]">
                        {value}
                      </dd>
                    </div>
                  ))}
                </dl>
                <div>
                  <h3 className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[#77746E]">
                    Customer explanation
                  </h3>
                  <p className="mt-1 whitespace-pre-wrap text-sm text-[#443F3A]">
                    {selectedReturn.reason_text ||
                      "No additional explanation provided."}
                  </p>
                </div>
                {selectedReturn.photo_urls.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {selectedReturn.photo_urls.map((url, index) => (
                      <a
                        key={url}
                        href={url}
                        target="_blank"
                        rel="noreferrer"
                        className="rounded-lg border border-[#E8E6E1] px-3 py-2 text-xs font-medium text-[#555048] hover:text-[#252525]"
                      >
                        View evidence {index + 1}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            )}
          </section>
        )}
      </div>
    </AppShell>
  );
}
