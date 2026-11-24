import React from "react";
import type { BackendReturn } from "@/lib/retail-api";
import { formatMoney } from "@/lib/utils";
import { buildViewModel } from "./ai-decision/buildViewModel";

interface ReturnDetailsCardProps {
  returnRecord: BackendReturn;
}

function getStatusBadge(status: string) {
  const s = status.toLowerCase();
  let bg = "bg-[#F3F2ED] text-[#6B6A63]";
  let label = "Pending review";

  if (s === "approved" || s === "refunded") {
    bg = "bg-[#E4F3E9] text-[#1E7A43]";
    label = s === "approved" ? "Approved" : "Refunded";
  } else if (s === "escalated" || s === "in_review" || s === "pending") {
    bg = "bg-[#FBF0D6] text-[#8A5A00]";
    label = s === "escalated" ? "Escalated" : "Pending review";
  } else if (s === "denied") {
    bg = "bg-[#FCE8E6] text-[#B3261E]";
    label = "Denied";
  }

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${bg}`}
    >
      {label}
    </span>
  );
}

export function ReturnDetailsCard({ returnRecord }: ReturnDetailsCardProps) {
  const vm = buildViewModel(returnRecord);

  // Derive styling for AI proposed decision text in grid
  let aiDecisionColor = "text-[#1F1E1B]";
  if (vm.outcome === "approve") aiDecisionColor = "text-[#1E7A43] font-semibold";
  else if (vm.outcome === "escalate") aiDecisionColor = "text-[#8A5A00] font-semibold";
  else if (vm.outcome === "deny") aiDecisionColor = "text-[#B3261E] font-semibold";

  return (
    <section className="rounded-2xl border border-[#E6E3DA] bg-white p-6 shadow-sm space-y-5">
      {/* Top Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
            Return Details
          </span>
          <h2 className="mt-1 font-mono text-base font-semibold text-[#1F1E1B] sm:text-lg break-all">
            {returnRecord.id}
          </h2>
        </div>
        <div>{getStatusBadge(returnRecord.status)}</div>
      </div>

      {/* 6 Key-Value Fields Grid */}
      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6 border-y border-[#E6E3DA] py-4">
        <div>
          <dt className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
            Order ID
          </dt>
          <dd className="mt-1 text-sm font-medium text-[#1F1E1B]">
            {returnRecord.order_id}
          </dd>
        </div>
        <div>
          <dt className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
            Order Item
          </dt>
          <dd className="mt-1 text-sm font-medium text-[#1F1E1B]">
            {returnRecord.order_item_id}
          </dd>
        </div>
        <div>
          <dt className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
            Reason
          </dt>
          <dd className="mt-1 text-sm font-medium text-[#1F1E1B]">
            {returnRecord.reason_code.replaceAll("_", " ")}
          </dd>
        </div>
        <div>
          <dt className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
            Amount
          </dt>
          <dd className="mt-1 text-sm font-bold text-[#1F1E1B] tabular-nums">
            {formatMoney(Number(returnRecord.amount))}
          </dd>
        </div>
        {vm.aiProposedDecision && (
          <div>
            <dt className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
              AI Proposed Decision
            </dt>
            <dd className={`mt-1 text-sm ${aiDecisionColor}`}>
              {vm.aiProposedDecision}
            </dd>
          </div>
        )}
        {returnRecord.final_decision && (
          <div>
            <dt className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
              Final Decision
            </dt>
            <dd className="mt-1 text-sm text-[#6B6A63]">
              {returnRecord.final_decision}
            </dd>
          </div>
        )}
      </dl>

      {/* Customer Explanation */}
      {returnRecord.reason_text && (
        <div>
          <h3 className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[#6B6A63]">
            Customer Explanation
          </h3>
          <p className="mt-1.5 text-sm text-[#1F1E1B] leading-relaxed">
            {returnRecord.reason_text}
          </p>
        </div>
      )}

      {/* Supporting Evidence Photos */}
      {returnRecord.photo_urls && returnRecord.photo_urls.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {returnRecord.photo_urls.map((url, idx) => (
            <a
              key={url}
              href={url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center rounded-lg border border-[#CFCBC0] bg-white px-3 py-1.5 text-xs font-medium text-[#1F1E1B] hover:bg-[#F3F2ED] transition"
            >
              View evidence {idx + 1}
            </a>
          ))}
        </div>
      )}
    </section>
  );
}
