"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ClipboardList,
  LayoutGrid,
  Package,
  RefreshCcw,
  ShieldCheck,
  Store,
  Truck,
} from "lucide-react";
import { useAppData } from "@/context/app-context";
import { cn } from "@/lib/utils";

interface SidebarProps {
  onCloseMobile?: () => void;
}

export function Sidebar({ onCloseMobile }: SidebarProps) {
  const pathname = usePathname();
  const { isAuthReady, summary, products, user } = useAppData();
  const isCustomer = user?.roles.includes("customer") ?? false;

  const navigationItems = [
    {
      href: "/dashboard",
      label: "Dashboard",
      icon: LayoutGrid,
      count: undefined,
    },
    {
      href: "/products",
      label: "Products",
      icon: Store,
      count: products.length,
    },
    ...(isAuthReady && isCustomer
      ? [
          {
            href: "/orders",
            label: "Orders",
            icon: Package,
            count: summary.totalOrders,
          },
          {
            href: "/refunds",
            label: "My Returns",
            icon: RefreshCcw,
            count:
              summary.pendingRefundRequests > 0
                ? summary.pendingRefundRequests
                : undefined,
            countHighlight: true,
          },
        ]
      : []),
    ...(user?.roles.some((role) => role === "admin" || role === "reviewer")
      ? [
          {
            href: "/returns",
            label: "Return Review",
            icon: ClipboardList,
            count: undefined,
          },
          {
            href: "/order-review",
            label: "Order Review",
            icon: Truck,
            count: undefined,
          },
        ]
      : []),
  ];

  return (
    <aside className="flex h-full flex-col justify-between p-5 bg-[#F1F0EC]">
      <div>
        {/* Brand Header */}
        <div className="flex items-center gap-3 px-2 py-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#D9D5CF] bg-white text-sm font-semibold tracking-[0.2em] text-[#585349] shadow-xs">
            M
          </div>
          <div>
            <div className="text-sm font-semibold uppercase tracking-[0.12em] text-[#5E5A54]">
              Marlow
            </div>
            <div className="text-[11px] text-[#77746E]">Commerce Operations</div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="mt-8 space-y-1.5" aria-label="Main Navigation">
          {navigationItems.map(
            ({ href, label, icon: Icon, count, countHighlight }) => {
              const active = pathname === href;

              return (
                <Link
                  key={href}
                  href={href}
                  onClick={onCloseMobile}
                  className={cn(
                    "group flex items-center justify-between rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-150",
                    active
                      ? "bg-white text-[#252525] shadow-xs ring-1 ring-[#E4E0DA]"
                      : "text-[#67635F] hover:bg-white/70 hover:text-[#252525]",
                  )}
                >
                  <div className="flex items-center gap-3">
                    <Icon
                      size={17}
                      className={cn(
                        "transition-colors",
                        active
                          ? "text-[#777D65]"
                          : "text-[#77746E] group-hover:text-[#252525]",
                      )}
                    />
                    <span>{label}</span>
                  </div>

                  {count !== undefined && (
                    <span
                      className={cn(
                        "rounded-full px-2 py-0.5 text-[10px] font-semibold tabular-nums",
                        countHighlight
                          ? "bg-[#FAF1D6] text-[#75591F] border border-[#EAD397]"
                          : "bg-[#EAE8E2] text-[#67635F]",
                      )}
                    >
                      {count}
                    </span>
                  )}
                </Link>
              );
            },
          )}
        </nav>
      </div>

      {/* Profile Section */}
      <div className="mt-8 rounded-2xl border border-[#E5E1DA] bg-white/90 p-3.5 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#E7E0D4] text-xs font-semibold text-[#443D35]">
            {user?.name
              .split(/\s+/)
              .map((part) => part[0])
              .join("")
              .slice(0, 2)
              .toUpperCase()}
            <span className="absolute -bottom-0.5 -right-0.5 block h-3 w-3 rounded-full border-2 border-white bg-[#777D65]" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-semibold text-[#252525]">
              {user?.name}
            </p>
            <div className="flex items-center gap-1 text-[11px] text-[#77746E]">
              <ShieldCheck size={12} className="text-[#777D65]" />
              <span className="truncate">
                {user?.role || "Account"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
