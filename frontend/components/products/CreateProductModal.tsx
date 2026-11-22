"use client";

import React, { useState, useRef } from "react";
import Image from "next/image";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { AlertCircle, Upload, X } from "lucide-react";

interface CreateProductModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (formData: FormData) => Promise<{
    success: boolean;
    message: string;
  }>;
}

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_IMAGE_BYTES = 5 * 1024 * 1024; // 5 MB

export function CreateProductModal({
  isOpen,
  onClose,
  onSubmit,
}: CreateProductModalProps) {
  if (!isOpen) return null;

  return <CreateProductModalInner onClose={onClose} onSubmit={onSubmit} />;
}

function CreateProductModalInner({
  onClose,
  onSubmit,
}: {
  onClose: () => void;
  onSubmit: (formData: FormData) => Promise<{
    success: boolean;
    message: string;
  }>;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("electronics");
  const [price, setPrice] = useState("");
  const [stock, setStock] = useState("100");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!ALLOWED_TYPES.includes(file.type)) {
      setError("Image must be JPEG, PNG or WebP format.");
      return;
    }

    if (file.size > MAX_IMAGE_BYTES) {
      setError("Image file cannot exceed 5 MB.");
      return;
    }

    setError("");
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!name.trim()) {
      setError("Product name is required (max 64 characters).");
      return;
    }
    if (name.trim().length > 64) {
      setError("Product name must be 64 characters or fewer.");
      return;
    }

    if (!description.trim()) {
      setError("Product description is required.");
      return;
    }

    if (!category.trim()) {
      setError("Category is required.");
      return;
    }

    const numPrice = parseFloat(price);
    if (isNaN(numPrice) || numPrice <= 0) {
      setError("Please enter a valid price greater than $0.00.");
      return;
    }

    const numStock = parseInt(stock, 10);
    if (isNaN(numStock) || numStock < 0) {
      setError("Stock quantity must be 0 or greater.");
      return;
    }

    if (!selectedFile) {
      setError("A product image file (JPEG, PNG, or WebP) is required.");
      return;
    }

    // Prepare FormData matching FastAPI Form(...) and File(...)
    const formData = new FormData();
    formData.append("name", name.trim());
    formData.append("description", description.trim());
    formData.append("category", category.trim());
    formData.append("price", numPrice.toFixed(2));
    formData.append("stock", String(numStock));
    formData.append("image", selectedFile);

    setIsSubmitting(true);
    const result = await onSubmit(formData);
    setIsSubmitting(false);

    if (result.success) {
      onClose();
    } else {
      setError(result.message);
    }
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      subtitle="Shop Management"
      title="Create New Product"
      maxWidth="md"
      footer={
        <>
          <Button
            variant="outline"
            size="md"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handleSubmit}
            isLoading={isSubmitting}
          >
            Upload to Shop
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Name */}
        <div>
          <label className="block text-xs font-semibold text-[#252525] mb-1">
            Product Name <span className="text-[#A24838]">*</span>
          </label>
          <input
            type="text"
            maxLength={64}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Ergonomic Keyboard Stand"
            className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3.5 py-2.5 text-xs text-[#252525] focus:border-[#777D65] focus:bg-white focus:outline-none transition-colors"
          />
        </div>

        {/* Category & Price */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-[#252525] mb-1">
              Category <span className="text-[#A24838]">*</span>
            </label>
            <input
              type="text"
              maxLength={60}
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="e.g. electronics"
              className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3.5 py-2.5 text-xs text-[#252525] focus:border-[#777D65] focus:bg-white focus:outline-none transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#252525] mb-1">
              Price ($) <span className="text-[#A24838]">*</span>
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="e.g. 79.99"
              className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3.5 py-2.5 text-xs text-[#252525] focus:border-[#777D65] focus:bg-white focus:outline-none transition-colors tabular-nums"
            />
          </div>
        </div>

        {/* Stock */}
        <div>
          <label className="block text-xs font-semibold text-[#252525] mb-1">
            Initial Stock Units <span className="text-[#A24838]">*</span>
          </label>
          <input
            type="number"
            min="0"
            value={stock}
            onChange={(e) => setStock(e.target.value)}
            className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3.5 py-2.5 text-xs text-[#252525] focus:border-[#777D65] focus:bg-white focus:outline-none transition-colors tabular-nums"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-xs font-semibold text-[#252525] mb-1">
            Product Description <span className="text-[#A24838]">*</span>
          </label>
          <textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Provide a detailed description of features and materials..."
            className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3.5 py-2.5 text-xs text-[#252525] focus:border-[#777D65] focus:bg-white focus:outline-none transition-colors resize-none leading-relaxed"
          />
        </div>

        {/* Image File Upload */}
        <div>
          <label className="block text-xs font-semibold text-[#252525] mb-1">
            Product Image (JPEG, PNG, WebP ≤ 5MB) <span className="text-[#A24838]">*</span>
          </label>

          {previewUrl ? (
            <div className="relative aspect-16/9 w-full overflow-hidden rounded-xl border border-[#E8E6E1] bg-[#F8F7F4]">
              <Image
                src={previewUrl}
                alt="Preview"
                fill
                className="object-cover"
                unoptimized
              />
              <button
                type="button"
                onClick={removeFile}
                className="absolute top-2 right-2 flex h-7 w-7 items-center justify-center rounded-full bg-[#1D1B1A]/70 text-white hover:bg-[#1D1B1A]"
              >
                <X size={14} />
              </button>
            </div>
          ) : (
            <div
              onClick={() => fileInputRef.current?.click()}
              className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-[#DDD7CD] bg-[#F8F7F4] p-5 text-center cursor-pointer transition hover:border-[#777D65] hover:bg-[#F2EFEA]"
            >
              <Upload size={20} className="text-[#8C8880] mb-1.5" />
              <p className="text-xs font-medium text-[#252525]">
                Click to browse product photo
              </p>
              <p className="text-[10px] text-[#77746E] mt-0.5">
                Saved directly to MinIO storage via FastAPI
              </p>
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={handleFileChange}
          />
        </div>

        {/* Error banner */}
        {error && (
          <div className="flex items-start gap-2 rounded-xl border border-[#E1B8B0] bg-[#EFD6D1] p-3 text-xs text-[#783D31]">
            <AlertCircle size={15} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
      </form>
    </Modal>
  );
}
