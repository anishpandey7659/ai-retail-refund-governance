"use client";

import React, { useMemo } from "react";
import {
  ShoppingBag,
  CircleDollarSign,
  AlertCircle,
  ClipboardCheck,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { StatCard } from "@/components/ui/StatCard";
import { RecentActivity } from "@/components/dashboard/RecentActivity";
import { useAppData } from "@/context/app-context";
import { formatMoney } from "@/lib/utils";

export default function DashboardPage() {
  const { orders, refundRequests, summary, accountError } = useAppData();

  const recentOrders = useMemo(() => {
    return [...orders]
      .sort(
        (a, b) =>
          new Date(b.orderDate).getTime() - new Date(a.orderDate).getTime(),
      )
      .slice(0, 5);
  }, [orders]);

  const recentRefunds = useMemo(() => {
    return [...refundRequests]
      .sort(
        (a, b) =>
          new Date(b.submissionDate).getTime() -
          new Date(a.submissionDate).getTime(),
      )
      .slice(0, 4);
  }, [refundRequests]);

  const statCards = [
    {
      label: "Total Orders",
      value: summary.totalOrders.toString(),
      detail: "Orders in your account",
      icon: ShoppingBag,
      accent: "bg-[#EAE8E2] text-[#4F4B44]",
    },
    {
      label: "Total Spending",
      value: formatMoney(summary.totalSpending),
      detail: "Total across your orders",
      icon: CircleDollarSign,
      accent: "bg-[#EFE7DC] text-[#5E4C3E]",
    },
    {
      label: "Pending Returns",
      value: summary.pendingRefundRequests.toString(),
      detail: "Awaiting an API decision",
      icon: AlertCircle,
      accent: "bg-[#FAF1D6] text-[#75591F]",
    },
    {
      label: "Completed Returns",
      value: summary.completedRefunds.toString(),
      detail: "Approved or denied by the API",
      icon: ClipboardCheck,
      accent: "bg-[#DFEAE0] text-[#2D4E35]",
    },
  ];

  return (
    <AppShell
      title="Dashboard"
      description="Overview of your orders and return requests loaded from the FastAPI service."
    >
      <div className="space-y-8">
        {accountError && (
          <div
            role="alert"
            className="rounded-xl border border-[#E1B8B0] bg-[#FBEBE8] p-3 text-sm text-[#783D31]"
          >
            Could not load the latest account data: {accountError}
          </div>
        )}
        {/* Metric Cards Grid */}
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {statCards.map((card) => (
            <StatCard
              key={card.label}
              label={card.label}
              value={card.value}
              detail={card.detail}
              icon={card.icon}
              accent={card.accent}
            />
          ))}
        </section>

        {/* Recent Activity Sections */}
        <RecentActivity
          recentOrders={recentOrders}
          recentRefunds={recentRefunds}
        />
      </div>
    </AppShell>
  );
}
