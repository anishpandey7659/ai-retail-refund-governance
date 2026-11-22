"use client";

import React from "react";
import Image from "next/image";
import { DataTable } from "@/components/ui/DataTable";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { type Order } from "@/types";
import { formatDate, formatMoney } from "@/lib/utils";
import { Eye, ShoppingBag } from "lucide-react";

interface OrdersTableProps {
  orders: Order[];
  onViewDetails: (order: Order) => void;
  onRequestRefund: (order: Order) => void;
}

const tableHeaders = [
  "Order ID",
  "Product",
  "Order Date",
  "Qty",
  "Total Price",
  "Order Status",
  "Return Status",
  "Actions",
];

export function OrdersTable({
  orders,
  onViewDetails,
  onRequestRefund,
}: OrdersTableProps) {
  return (
    <DataTable
      headers={tableHeaders}
      isEmpty={orders.length === 0}
      emptyTitle="No orders found"
      emptyDescription="Try adjusting your search query or status filters."
    >
      {orders.map((order) => {
        const canRequestRefund =
          order.refundStatus === "Not Requested" ||
          order.refundStatus === "Denied";

        return (
          <tr
            key={order.orderItemId}
            className="transition-colors hover:bg-[#FAF9F7] group"
          >
            {/* Order ID */}
            <td className="px-4 py-3.5 sm:px-5 font-semibold text-[#252525] whitespace-nowrap">
              {order.id}
            </td>

            {/* Product */}
            <td className="px-4 py-3.5 sm:px-5">
              <div className="flex items-center gap-3">
                <div className="relative h-10 w-10 overflow-hidden rounded-xl border border-[#E8E6E1] bg-white shrink-0">
                  {order.product.image ? (
                    <Image
                      src={order.product.image}
                      alt={order.product.name}
                      fill
                      className="object-cover"
                      sizes="40px"
                      unoptimized
                    />
                  ) : (
                    <div
                      className={`flex h-full w-full items-center justify-center font-bold text-xs ${order.product.tone}`}
                    >
                      {order.product.name.slice(0, 2).toUpperCase()}
                    </div>
                  )}
                </div>
                <div className="min-w-0 max-w-[200px] sm:max-w-xs">
                  <p className="truncate font-medium text-[#252525]">
                    {order.product.name}
                  </p>
                  <p className="truncate text-[11px] text-[#77746E]">
                    {order.customer.name}
                  </p>
                </div>
              </div>
            </td>

            {/* Order Date */}
            <td className="px-4 py-3.5 sm:px-5 whitespace-nowrap text-xs text-[#67635F]">
              {formatDate(order.orderDate)}
            </td>

            {/* Quantity */}
            <td className="px-4 py-3.5 sm:px-5 whitespace-nowrap text-xs font-medium text-[#252525] tabular-nums">
              {order.quantity}
            </td>

            {/* Total Price */}
            <td className="px-4 py-3.5 sm:px-5 whitespace-nowrap text-xs font-semibold text-[#252525] tabular-nums">
              {formatMoney(order.totalPrice)}
            </td>

            {/* Order Status */}
            <td className="px-4 py-3.5 sm:px-5 whitespace-nowrap">
              <Badge status={order.orderStatus} size="sm" />
            </td>

            {/* Return Status */}
            <td className="px-4 py-3.5 sm:px-5 whitespace-nowrap">
              <Badge status={order.refundStatus} size="sm" />
            </td>

            {/* Actions */}
            <td className="px-4 py-3.5 sm:px-5 whitespace-nowrap text-right">
              <div className="inline-flex items-center gap-1.5">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onViewDetails(order)}
                >
                  <Eye size={13} />
                  <span>View Details</span>
                </Button>

                {canRequestRefund ? (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => onRequestRefund(order)}
                  >
                    <ShoppingBag size={13} />
                    <span>Request Return</span>
                  </Button>
                ) : (
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled
                    className="cursor-default opacity-60"
                  >
                    {order.refundStatus === "Pending Review"
                      ? "In Review"
                      : order.refundStatus === "Denied"
                        ? "Denied"
                        : order.refundStatus === "Refunded"
                          ? "Refunded"
                          : "Return approved"}
                  </Button>
                )}
              </div>
            </td>
          </tr>
        );
      })}
    </DataTable>
  );
}
