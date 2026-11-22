"use client";

import React, { useMemo, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { ProductCard } from "@/components/products/ProductCard";
import { ProductDetailsModal } from "@/components/products/ProductDetailsModal";
import { OrderProductModal } from "@/components/products/OrderProductModal";
import { CreateProductModal } from "@/components/products/CreateProductModal";
import { Button } from "@/components/ui/Button";
import { useAppData } from "@/context/app-context";
import { type Product } from "@/types";
import {
  getProductById,
  mapBackendProductToFrontend,
} from "@/lib/shop-api";
import {
  Search,
  Plus,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Store,
} from "lucide-react";

export default function ProductsPage() {
  const {
    products,
    isBackendOnline,
    backendError,
    refreshProducts,
    createBackendProduct,
    createProductOrder,
    showToast,
    isAuthReady,
    user,
  } = useAppData();

  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [orderProduct, setOrderProduct] = useState<Product | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleViewDetails = async (product: Product) => {
    setSelectedProduct(product);
    const response = await getProductById(product.id);
    if (response.success && response.data) {
      setSelectedProduct(mapBackendProductToFrontend(response.data));
      return;
    }

    showToast(
      response.error || `Could not refresh image for "${product.name}".`,
      "error",
    );
  };

  // Derive unique categories from existing products
  const categories = useMemo(() => {
    const set = new Set<string>();
    products.forEach((p) => {
      if (p.category) set.add(p.category.toLowerCase());
    });
    return ["All", ...Array.from(set)];
  }, [products]);

  // Filtered products list
  const filteredProducts = useMemo(() => {
    const q = searchTerm.trim().toLowerCase();

    return products.filter((product) => {
      const matchesSearch =
        q.length === 0 ||
        product.name.toLowerCase().includes(q) ||
        (product.description && product.description.toLowerCase().includes(q)) ||
        product.category.toLowerCase().includes(q);

      const matchesCat =
        selectedCategory === "All" ||
        product.category.toLowerCase() === selectedCategory.toLowerCase();

      return matchesSearch && matchesCat;
    });
  }, [products, searchTerm, selectedCategory]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refreshProducts();
    setIsRefreshing(false);
  };

  const isCustomer = isAuthReady && (user?.roles.includes("customer") ?? false);

  return (
    <AppShell
      title="Shop Products"
      description="Directly connected to FastAPI shop_router (GET /products, POST /products, GET /products/{id})."
    >
      <div className="space-y-6">
        {/* Backend API Connection Status Banner */}
        <div
          className={`rounded-2xl border p-4 shadow-[0_1px_2px_rgba(0,0,0,0.02)] transition-colors ${
            isBackendOnline
              ? "border-[#D1E3CC] bg-[#EBF3E8]/80 text-[#2D4E35]"
              : "border-[#EAD397] bg-[#FAF1D6]/70 text-[#75591F]"
          }`}
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              {isBackendOnline ? (
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#DFEAE0] text-[#2D4E35] shrink-0">
                  <CheckCircle2 size={16} />
                </div>
              ) : (
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#F5E5C3] text-[#75591F] shrink-0">
                  <AlertTriangle size={16} />
                </div>
              )}

              <div>
                <p className="text-xs font-semibold">
                  {isBackendOnline
                    ? "FastAPI Shop API Connected"
                    : isBackendOnline === null
                      ? "Connecting to FastAPI..."
                      : "FastAPI Backend Offline"}
                </p>
                <p className="text-[11px] opacity-85 mt-0.5">
                  {isBackendOnline
                    ? "Live communication with http://127.0.0.1:8000/products and MinIO image storage."
                    : backendError || "The API catalog is unavailable. No demo catalog is shown."}
                </p>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              isLoading={isRefreshing}
              className="self-start sm:self-auto bg-white/90 border-[#D6D1C7]"
            >
              <RefreshCw size={13} />
              <span>Probe Backend</span>
            </Button>
          </div>
        </div>

        {/* Toolbar & Filters */}
        <div className="rounded-2xl border border-[#E8E6E1] bg-white p-4 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            {/* Search Input */}
            <div className="relative w-full lg:max-w-md">
              <Search
                size={16}
                className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[#8C8880]"
              />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search products by title, category, or spec..."
                className="w-full rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] py-2.5 pl-10 pr-3.5 text-xs text-[#252525] placeholder:text-[#8C8880] focus:border-[#777D65] focus:bg-white focus:outline-none transition-colors"
              />
            </div>

            {/* Actions: Category select + Add Product */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#77746E]">
                  Category:
                </span>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="rounded-xl border border-[#E8E6E1] bg-[#F8F7F4] px-3 py-2 text-xs text-[#252525] focus:border-[#777D65] focus:bg-white focus:outline-none transition-colors cursor-pointer capitalize"
                >
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat === "All" ? "All Categories" : cat}
                    </option>
                  ))}
                </select>
              </div>

              <Button
                variant="primary"
                size="md"
                onClick={() => setIsCreateOpen(true)}
              >
                <Plus size={15} />
                <span>Add Product</span>
              </Button>
            </div>
          </div>
        </div>

        {/* Products Grid */}
        {filteredProducts.length === 0 ? (
          <div className="rounded-2xl border border-[#E8E6E1] bg-white p-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-[#E8E6E1] bg-[#F8F7F4] text-[#8C8880]">
              <Store size={24} />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-[#252525]">
              No products found
            </h3>
            <p className="mt-1 text-xs text-[#77746E]">
              Try adjusting your search criteria or create a new product above.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredProducts.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                canOrder={isCustomer}
                onOrder={setOrderProduct}
                onViewDetails={(p) => void handleViewDetails(p)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Product Details Modal (GET /products/{id}) */}
      <ProductDetailsModal
        product={selectedProduct}
        isOpen={Boolean(selectedProduct)}
        onClose={() => setSelectedProduct(null)}
      />

      <OrderProductModal
        product={orderProduct}
        isOpen={Boolean(orderProduct) && isCustomer}
        onClose={() => setOrderProduct(null)}
        onSubmit={createProductOrder}
      />

      {/* Create Product Modal (POST /products) */}
      <CreateProductModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSubmit={createBackendProduct}
      />
    </AppShell>
  );
}
