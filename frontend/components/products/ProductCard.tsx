"use client";

import React, { useState } from "react";
import Image from "next/image";
import { type Product } from "@/types";
import { formatMoney } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Eye, Package, ShoppingBag } from "lucide-react";

interface ProductCardProps {
  product: Product;
  onViewDetails: (product: Product) => void;
  canOrder: boolean;
  onOrder: (product: Product) => void;
}

export function ProductCard({
  product,
  onViewDetails,
  canOrder,
  onOrder,
}: ProductCardProps) {
  const [imageError, setImageError] = useState(false);

  const stock = product.stock ?? 100;
  const isOutOfStock = stock <= 0;
  const isLowStock = stock > 0 && stock <= 15;

  return (
    <div className="group flex flex-col justify-between overflow-hidden rounded-2xl border border-[#E8E6E1] bg-white p-4 shadow-[0_1px_2px_rgba(0,0,0,0.02)] transition-all hover:border-[#D6D1C7] hover:shadow-[0_8px_20px_rgba(30,27,24,0.05)]">
      <div>
        {/* Product Image */}
        <div className="relative aspect-4/3 w-full overflow-hidden rounded-xl border border-[#EAE6DF] bg-[#F8F7F4]">
          {product.image && !imageError ? (
            <Image
              src={product.image}
              alt={product.name}
              fill
              className="object-cover transition-transform duration-300 group-hover:scale-105"
              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
              onError={() => setImageError(true)}
              unoptimized
            />
          ) : (
            <div
              className={`flex h-full w-full flex-col items-center justify-center font-bold text-lg ${product.tone}`}
            >
              <Package size={32} className="opacity-40 mb-1" />
              <span>{product.name.slice(0, 2).toUpperCase()}</span>
            </div>
          )}

          {/* Category Tag */}
          <div className="absolute top-2.5 left-2.5">
            <span className="rounded-full bg-white/90 backdrop-blur-xs px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-[#5E5A54] shadow-xs border border-[#E8E6E1]">
              {product.category}
            </span>
          </div>

          {/* Stock Tag */}
          <div className="absolute top-2.5 right-2.5">
            {isOutOfStock ? (
              <span className="rounded-full bg-[#EFD6D1] px-2 py-0.5 text-[10px] font-semibold text-[#783D31] border border-[#E1B8B0]">
                Out of Stock
              </span>
            ) : isLowStock ? (
              <span className="rounded-full bg-[#FAF1D6] px-2 py-0.5 text-[10px] font-semibold text-[#75591F] border border-[#EAD397]">
                Only {stock} left
              </span>
            ) : (
              <span className="rounded-full bg-[#DFEAE0] px-2 py-0.5 text-[10px] font-semibold text-[#2D4E35] border border-[#BED2C1]">
                In Stock ({stock})
              </span>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="mt-3.5 space-y-1.5">
          <h3 className="text-sm font-semibold text-[#252525] group-hover:text-[#777D65] transition-colors truncate">
            {product.name}
          </h3>

          <p className="text-xs text-[#77746E] line-clamp-2 leading-relaxed h-8">
            {product.description || "No description provided."}
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#F0ECE7]">
        <div>
          <span className="text-[10px] uppercase tracking-wider text-[#77746E] block">
            Price
          </span>
          <span className="text-base font-bold text-[#252525] tabular-nums">
            {formatMoney(product.price)}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {canOrder && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => onOrder(product)}
              disabled={isOutOfStock}
            >
              <ShoppingBag size={13} />
              <span>Order</span>
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => onViewDetails(product)}
          >
            <Eye size={13} />
            <span>Details</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
