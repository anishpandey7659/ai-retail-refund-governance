"use client";

import React, { useState } from "react";
import { AlertCircle, CreditCard, MapPin } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { formatMoney } from "@/lib/utils";
import { type Product } from "@/types";
import { type CreateOrderInput } from "@/lib/retail-api";

interface OrderProductModalProps {
  product: Product | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (input: CreateOrderInput) => Promise<{
    success: boolean;
    message: string;
  }>;
}

export function OrderProductModal({
  product,
  isOpen,
  onClose,
  onSubmit,
}: OrderProductModalProps) {
  if (!isOpen || !product) return null;

  return (
    <OrderProductModalForm
      key={product.id}
      product={product}
      onClose={onClose}
      onSubmit={onSubmit}
    />
  );
}

function OrderProductModalForm({
  product,
  onClose,
  onSubmit,
}: Omit<OrderProductModalProps, "isOpen" | "product"> & {
  product: Product;
}) {
  const stock = product.stock ?? 100;
  const maxQuantity = Math.min(stock, 20);
  const [quantity, setQuantity] = useState("1");
  const [shippingAddress, setShippingAddress] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [cardExp, setCardExp] = useState("");
  const [cardCvc, setCardCvc] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");

    const parsedQuantity = Number(quantity);
    if (
      !Number.isInteger(parsedQuantity) ||
      parsedQuantity < 1 ||
      parsedQuantity > maxQuantity
    ) {
      setError(`Choose a quantity between 1 and ${maxQuantity}.`);
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await onSubmit({
        productId: product.id,
        quantity: parsedQuantity,
        shippingAddress: shippingAddress.trim(),
        cardNumber: cardNumber.trim(),
        cardExp: cardExp.trim(),
        cardCvc: cardCvc.trim(),
      });
      if (result.success) {
        onClose();
      } else {
        setError(result.message);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen
      onClose={onClose}
      subtitle="Customer checkout"
      title={`Order ${product.name}`}
      maxWidth="md"
      footer={
        <>
          <Button
            type="button"
            variant="outline"
            size="md"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            form="product-checkout-form"
            variant="primary"
            size="md"
            isLoading={isSubmitting}
            disabled={maxQuantity === 0}
          >
            Place order
          </Button>
        </>
      }
    >
      <form
        id="product-checkout-form"
        onSubmit={(event) => void handleSubmit(event)}
        className="space-y-5"
      >
        <div className="flex items-center justify-between rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] p-4">
          <div>
            <p className="text-sm font-semibold text-[#252525]">{product.name}</p>
            <p className="mt-1 text-xs text-[#77746E]">
              {formatMoney(product.price)} each · {stock} available
            </p>
          </div>
          <div className="w-24">
            <label
              htmlFor="order-quantity"
              className="mb-1 block text-[11px] font-semibold text-[#5E5A54]"
            >
              Quantity
            </label>
            <input
              id="order-quantity"
              type="number"
              min="1"
              max={maxQuantity}
              value={quantity}
              onChange={(event) => setQuantity(event.target.value)}
              required
              disabled={maxQuantity === 0}
              className="w-full rounded-lg border border-[#E8E6E1] bg-white px-2.5 py-2 text-sm tabular-nums focus:border-[#777D65] focus:outline-none"
            />
          </div>
        </div>

        <div className="space-y-3">
          <label
            htmlFor="shipping-address"
            className="flex items-center gap-2 text-xs font-semibold text-[#252525]"
          >
            <MapPin size={14} className="text-[#777D65]" />
            Shipping address
          </label>
          <textarea
            id="shipping-address"
            value={shippingAddress}
            onChange={(event) => setShippingAddress(event.target.value)}
            required
            rows={3}
            autoComplete="street-address"
            placeholder="Enter your delivery address"
            className="w-full resize-y rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3.5 py-2.5 text-xs focus:border-[#777D65] focus:bg-white focus:outline-none"
          />
        </div>

        <fieldset className="space-y-3">
          <legend className="flex items-center gap-2 text-xs font-semibold text-[#252525]">
            <CreditCard size={14} className="text-[#777D65]" />
            Mock payment details
          </legend>
          <p className="text-[11px] leading-relaxed text-[#77746E]">
            This demo validates a test card only. Card details are sent for
            checkout and are not saved.
          </p>
          <label htmlFor="card-number" className="sr-only">
            Card number
          </label>
          <input
            id="card-number"
            type="text"
            inputMode="numeric"
            autoComplete="cc-number"
            value={cardNumber}
            onChange={(event) => setCardNumber(event.target.value)}
            required
            maxLength={23}
            placeholder="Card number (test card: 4242 4242 4242 4242)"
            className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3.5 py-2.5 text-xs focus:border-[#777D65] focus:bg-white focus:outline-none"
          />
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label
                htmlFor="card-expiry"
                className="mb-1 block text-[11px] font-semibold text-[#5E5A54]"
              >
                Expiry
              </label>
              <input
                id="card-expiry"
                type="text"
                autoComplete="cc-exp"
                value={cardExp}
                onChange={(event) => setCardExp(event.target.value)}
                required
                placeholder="MM/YY"
                className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3.5 py-2.5 text-xs focus:border-[#777D65] focus:bg-white focus:outline-none"
              />
            </div>
            <div>
              <label
                htmlFor="card-cvc"
                className="mb-1 block text-[11px] font-semibold text-[#5E5A54]"
              >
                CVC
              </label>
              <input
                id="card-cvc"
                type="password"
                inputMode="numeric"
                autoComplete="cc-csc"
                value={cardCvc}
                onChange={(event) => setCardCvc(event.target.value)}
                required
                minLength={3}
                maxLength={4}
                placeholder="3–4 digits"
                className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3.5 py-2.5 text-xs focus:border-[#777D65] focus:bg-white focus:outline-none"
              />
            </div>
          </div>
        </fieldset>

        <div className="flex items-center justify-between border-t border-[#F0ECE7] pt-4">
          <span className="text-xs font-semibold text-[#5E5A54]">
            Order total
          </span>
          <span className="text-lg font-bold tabular-nums text-[#252525]">
            {formatMoney(product.price * (Number(quantity) || 0))}
          </span>
        </div>

        {maxQuantity === 0 && (
          <p role="alert" className="text-xs text-[#783D31]">
            This product is out of stock.
          </p>
        )}
        {error && (
          <div
            role="alert"
            className="flex items-start gap-2 rounded-xl border border-[#E1B8B0] bg-[#FBEBE8] p-3 text-xs text-[#783D31]"
          >
            <AlertCircle size={15} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </form>
    </Modal>
  );
}
