"use client";

import React from "react";
import Image from "next/image";
import { DataTable } from "@/components/ui/DataTable";
import { Badge } from "@/components/ui/Badge";
import { type RefundRequest } from "@/types";
import { formatDate, formatMoney } from "@/lib/utils";
import { Eye } from "lucide-react";

interface RefundsTableProps {
  refundRequests: RefundRequest[];
  onViewDetails: (request: RefundRequest) => void;
}

const tableHeaders = [
  "Return ID",
  "Order ID",
  "Customer",
  "Product",
  "Return Amount",
  "Reason",
  "Date",
  "Status",
  "Actions",
];

export function RefundsTable({
  refundRequests,
  onViewDetails,
}: RefundsTableProps) {
  return (
    <DataTable
      headers={tableHeaders}
      isEmpty={refundRequests.length === 0}
      emptyTitle="No return requests found"
      emptyDescription="No return requests match your current search query or filter selection."
    >
      {refundRequests.map((request) => {
        return (
          <tr
            key={request.id}
            className="transition-colors hover:bg-[#FAF9F7] group"
          >
            {/* Return ID */}
            <td className="px-4 py-3.5 sm:px-5 font-semibold text-[#252525] whitespace-nowrap">
              {request.id}
            </td>

            {/* Order ID */}
            <td className="px-4 py-3.5 sm:px-5 text-xs text-[#555048] whitespace-nowrap">
              {request.orderId}
            </td>

            {/* Customer Name */}
            <td className="px-4 py-3.5 sm:px-5 whitespace-nowrap">
              <div className="text-xs font-semibold text-[#252525]">
                {request.customer.name}
              </div>
              <div className="text-[10px] text-[#77746E]">
                {request.customer.email}
              </div>
            </td>

            {/* Product */}
            <td className="px-4 py-3.5 sm:px-5">
              <div className="flex items-center gap-2.5">
                <div className="relative h-8 w-8 overflow-hidden rounded-lg border border-[#E8E6E1] bg-white shrink-0">
                  {request.product.image ? (
                    <Image
                      src={request.product.image}
                      alt={request.product.name}
                      fill
                      className="object-cover"
                      sizes="32px"
                      unoptimized
                    />
                  ) : (
                    <div
                      className={`flex h-full w-full items-center justify-center font-bold text-[10px] ${request.product.tone}`}
                    >
                      {request.product.name.slice(0, 2).toUpperCase()}
                    </div>
                  )}
                </div>
                <span className="truncate max-w-[140px] text-xs font-medium text-[#252525]">
                  {request.product.name}
                </span>
              </div>
            </td>

            {/* Requested Amount */}
            <td className="px-4 py-3.5 sm:px-5 whitespace-nowrap text-xs font-semibold text-[#252525] tabular-nums">
              {formatMoney(request.requestedAmount)}
            </td>

            {/* Reason */}
            <td className="px-4 py-3.5 sm:px-5 text-xs text-[#67635F] max-w-[150px] truncate">
              {request.reason}
            </td>

            {/* Submission Date */}
            <td className="px-4 py-3.5 sm:px-5 whitespace-nowrap text-xs text-[#77746E]">
              {formatDate(request.submissionDate)}
            </td>

            {/* Status */}
            <td className="px-4 py-3.5 sm:px-5 whitespace-nowrap">
              <Badge status={request.reviewStatus} size="sm" />
            </td>

            {/* Actions */}
            <td className="px-4 py-3.5 sm:px-5 whitespace-nowrap text-right">
              <button
                type="button"
                onClick={() => onViewDetails(request)}
                className="inline-flex items-center gap-1.5 rounded-lg border border-[#E8E6E1] bg-white px-3 py-2 text-xs font-medium text-[#555048] hover:text-[#252525]"
              >
                <Eye size={13} />
                <span>View Details</span>
              </button>
            </td>
          </tr>
        );
      })}
    </DataTable>
  );
}
