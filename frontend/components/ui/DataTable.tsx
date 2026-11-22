import React from "react";
import { cn } from "@/lib/utils";
import { Inbox } from "lucide-react";

interface DataTableProps {
  headers: string[];
  children: React.ReactNode;
  isEmpty?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  className?: string;
}

export function DataTable({
  headers,
  children,
  isEmpty = false,
  emptyTitle = "No records found",
  emptyDescription = "There are no entries matching your current search or filters.",
  className,
}: DataTableProps) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-2xl border border-[#E8E6E1] bg-white shadow-[0_1px_2px_rgba(0,0,0,0.02)]",
        className,
      )}
    >
      <div className="overflow-x-auto">
        <table className="min-w-full text-left">
          <thead className="border-b border-[#F0ECE7] bg-[#F8F7F4] text-[11px] font-semibold uppercase tracking-[0.12em] text-[#77746E]">
            <tr>
              {headers.map((header, index) => (
                <th
                  key={index}
                  className={cn(
                    "px-4 py-3.5 sm:px-5",
                    index === headers.length - 1 ? "text-right" : "",
                  )}
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#F0ECE7] text-sm text-[#3E3A37]">
            {isEmpty ? (
              <tr>
                <td colSpan={headers.length} className="px-6 py-16 text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-[#E8E6E1] bg-[#F8F7F4] text-[#8C8880]">
                    <Inbox size={22} />
                  </div>
                  <h4 className="mt-3.5 text-sm font-semibold text-[#252525]">
                    {emptyTitle}
                  </h4>
                  <p className="mt-1 text-xs text-[#77746E] max-w-sm mx-auto">
                    {emptyDescription}
                  </p>
                </td>
              </tr>
            ) : (
              children
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
