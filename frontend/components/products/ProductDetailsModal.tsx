"use client";

import React, { useState } from "react";
import Image from "next/image";
import { type Product } from "@/types";
import { formatMoney } from "@/lib/utils";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Package, Hash, Tag, Layers, CheckCircle2 } from "lucide-react";

interface ProductDetailsModalProps {
  product: Product | null;
  isOpen: boolean;
  onClose: () => void;
}

export function ProductDetailsModal({
  product,
  isOpen,
  onClose,
}: ProductDetailsModalProps) {
  const [failedImageUrl, setFailedImageUrl] = useState<string | null>(null);

  if (!product) return null;

  const stock = product.stock ?? 100;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      subtitle="Product Specification"
      title={product.name}
      maxWidth="lg"
      footer={
        <div className="flex items-center justify-between w-full">
          <span className="text-xs text-[#77746E]">
            ID: <span className="font-mono text-[#252525]">{product.id}</span>
          </span>
          <Button variant="outline" size="md" onClick={onClose}>
            Close
          </Button>
        </div>
      }
    >
      <div className="space-y-5">
        {/* Large Product Image */}
        <div className="relative aspect-16/9 w-full overflow-hidden rounded-2xl border border-[#E8E6E1] bg-[#F8F7F4]">
          {product.image && failedImageUrl !== product.image ? (
            <Image
              src={product.image}
              alt={product.name}
              fill
              className="object-cover"
              sizes="600px"
              onError={() => setFailedImageUrl(product.image)}
              unoptimized
            />
          ) : (
            <div
              className={`flex h-full w-full flex-col items-center justify-center font-bold text-2xl ${product.tone}`}
            >
              <Package size={48} className="opacity-30 mb-2" />
              <span>{product.name}</span>
            </div>
          )}
        </div>

        {/* Info Grid */}
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-[#E9E5DF] bg-[#F8F7F4] p-3 text-xs">
            <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-[#77746E]">
              <Tag size={12} /> Category
            </div>
            <div className="mt-1 font-semibold text-[#252525] capitalize">
              {product.category}
            </div>
          </div>

          <div className="rounded-xl border border-[#E9E5DF] bg-[#F8F7F4] p-3 text-xs">
            <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-[#77746E]">
              <Hash size={12} /> Unit Price
            </div>
            <div className="mt-1 font-semibold text-[#252525] tabular-nums">
              {formatMoney(product.price)}
            </div>
          </div>

          <div className="rounded-xl border border-[#E9E5DF] bg-[#F8F7F4] p-3 text-xs">
            <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-[#77746E]">
              <Layers size={12} /> Available Stock
            </div>
            <div className="mt-1 font-semibold text-[#252525] tabular-nums">
              {stock} units
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="rounded-xl border border-[#E9E5DF] p-4 text-xs">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[#77746E] block mb-1.5">
            Product Description
          </span>
          <p className="text-[#3E3A37] leading-relaxed">
            {product.description ||
              "No long-form description available for this item."}
          </p>
        </div>

        {/* Backend Synced Note */}
        <div className="rounded-xl border border-[#D1E3CC] bg-[#EBF3E8] p-3 text-xs text-[#2D4E35] flex items-center gap-2">
          <CheckCircle2 size={15} className="shrink-0" />
          <span>
            Connected to FastAPI Shop API (<code className="font-mono text-[11px]">/products/{product.id}</code>).
          </span>
        </div>
      </div>
    </Modal>
  );
}
