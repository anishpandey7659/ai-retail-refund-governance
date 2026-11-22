import { type BackendProductOut, type Product } from "@/types";
import { getCurrentAccessToken } from "@/lib/keycloak";

// Base URL for FastAPI backend.
// In Next.js client, defaults to direct backend (http://127.0.0.1:8000) or relative /api/proxy.
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface FetchProductsParams {
  category?: string;
  limit?: number;
  offset?: number;
}

export function mapBackendProductToFrontend(
  bp: BackendProductOut,
  index = 0,
): Product {
  const tones = [
    "bg-[#EFE5DB] text-[#4D3B2E]",
    "bg-[#E4E1DB] text-[#3E403D]",
    "bg-[#E1E7DF] text-[#39453A]",
    "bg-[#F3EAD8] text-[#5A4836]",
    "bg-[#E8E1D9] text-[#483F3D]",
    "bg-[#E9E4D9] text-[#473F38]",
    "bg-[#E2E6E8] text-[#33444C]",
  ];

  const tone = tones[index % tones.length];

  return {
    id: bp.id,
    name: bp.name,
    category: bp.category,
    price: typeof bp.price === "number" ? bp.price : parseFloat(bp.price) || 0,
    image: bp.image_url || "",
    image_url: bp.image_url,
    tone,
    description: bp.description,
    stock: bp.stock,
  };
}

/**
 * Fetch products from FastAPI shop_router (GET /products)
 */
export async function getProducts(
  params?: FetchProductsParams,
): Promise<{ success: boolean; data: BackendProductOut[]; error?: string }> {
  try {
    const query = new URLSearchParams();
    if (params?.category) query.append("category", params.category);
    if (params?.limit) query.append("limit", String(params.limit));
    if (params?.offset) query.append("offset", String(params.offset));

    const qs = query.toString();
    const url = `${API_BASE_URL}/products${qs ? `?${qs}` : ""}`;

    const res = await fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      // cache: "no-store"
    });

    if (!res.ok) {
      const errText = await res.text();
      return {
        success: false,
        data: [],
        error: `FastAPI responded with HTTP ${res.status}: ${errText}`,
      };
    }

    const json = (await res.json()) as BackendProductOut[];
    return { success: true, data: json };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return {
      success: false,
      data: [],
      error: `Could not connect to FastAPI backend at ${API_BASE_URL}: ${msg}`,
    };
  }
}

/**
 * Fetch single product from FastAPI shop_router (GET /products/{product_id})
 */
export async function getProductById(
  productId: string,
): Promise<{ success: boolean; data?: BackendProductOut; error?: string }> {
  try {
    const url = `${API_BASE_URL}/products/${productId}`;
    const res = await fetch(url, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });

    if (!res.ok) {
      const errText = await res.text();
      return {
        success: false,
        error: `FastAPI responded with HTTP ${res.status}: ${errText}`,
      };
    }

    const json = (await res.json()) as BackendProductOut;
    return { success: true, data: json };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return {
      success: false,
      error: `Could not connect to FastAPI backend: ${msg}`,
    };
  }
}

/**
 * Create product via FastAPI shop_router (POST /products)
 * Expects multipart/form-data: name, description, category, price, image, stock
 */
export async function createProduct(
  formData: FormData,
): Promise<{ success: boolean; data?: BackendProductOut; error?: string }> {
  try {
    const url = `${API_BASE_URL}/products`;
    const accessToken = await getCurrentAccessToken();
    if (!accessToken) {
      return { success: false, error: "Please sign in to create a product." };
    }
    const res = await fetch(url, {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
      body: formData,
      // Do not manually set Content-Type header so the browser sets the boundary
    });

    if (!res.ok) {
      let errorDetail = `HTTP ${res.status}`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          errorDetail =
            typeof errorJson.detail === "string"
              ? errorJson.detail
              : JSON.stringify(errorJson.detail);
        }
      } catch {
        errorDetail = await res.text();
      }
      return {
        success: false,
        error: errorDetail,
      };
    }

    const json = (await res.json()) as BackendProductOut;
    return { success: true, data: json };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return {
      success: false,
      error: `Failed to create product on FastAPI backend: ${msg}`,
    };
  }
}

/**
 * Check if the FastAPI backend is running and healthy
 */
export async function checkBackendHealth(): Promise<{
  online: boolean;
  url: string;
  details?: string;
}> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 2000);

    const res = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      signal: controller.signal,
    });
    clearTimeout(timeout);

    if (res.ok) {
      return { online: true, url: API_BASE_URL };
    }
    return {
      online: false,
      url: API_BASE_URL,
      details: `Health check status: ${res.status}`,
    };
  } catch (err: unknown) {
    return {
      online: false,
      url: API_BASE_URL,
      details: err instanceof Error ? err.message : String(err),
    };
  }
}
