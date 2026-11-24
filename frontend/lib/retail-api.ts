import { API_BASE_URL } from "@/lib/shop-api";
import { getCurrentAccessToken } from "@/lib/keycloak";

export interface CurrentUser {
  user_id: string;
  name: string;
  email: string;
  role: string;
  roles: string[];
}

export interface BackendOrderItem {
  id: string;
  product_id: string;
  name: string;
  unit_price: number | string;
  qty: number;
}

export interface BackendOrder {
  id: string;
  status: string;
  total: number | string;
  payment_last4: string;
  placed_at: string;
  items: BackendOrderItem[];
}

export interface BackendReviewOrder extends BackendOrder {
  customer_name: string;
  customer_email: string;
  shipping_address: string;
}

export interface CreateOrderInput {
  productId: string;
  quantity: number;
  shippingAddress: string;
  cardNumber: string;
  cardExp: string;
  cardCvc: string;
}

export interface BackendReturn {
  id: string;
  order_id: string;
  order_item_id: string;
  reason_code: string;
  reason_text: string;
  status: string;
  amount: number | string;
  // agent_results: full pipeline output dict[agent_name, AgentResult] from the worker.
  // Replaces the old ai_proposed_decision: string field. See types in
  // frontend/components/returns/ai-decision/types.ts for the shape.
  agent_results: Record<string, unknown> | null;
  final_decision: string | null;
  created_at: string;
  photo_urls: string[];
}

export interface CreateReturnInput {
  orderItemId: string;
  reasonCode: string;
  reasonText: string;
  photo: File;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function getErrorMessage(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    const body: unknown = await response.json();
    if (
      typeof body === "object" &&
      body !== null &&
      "detail" in body &&
      typeof body.detail === "string"
    ) {
      return body.detail;
    }
    return JSON.stringify(body);
  }
  return (await response.text()) || `HTTP ${response.status}`;
}

async function request<T>(
  path: string,
  init?: RequestInit,
  accessToken?: string,
): Promise<T> {
  let response: Response;
  try {
    const currentToken = (await getCurrentAccessToken()) ?? accessToken;
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(currentToken ? { Authorization: `Bearer ${currentToken}` } : {}),
        ...init?.headers,
      },
      cache: "no-store",
    });
  } catch (error: unknown) {
    throw new ApiError(
      error instanceof Error ? error.message : "Could not connect to the API.",
    );
  }

  if (!response.ok) {
    const message = await getErrorMessage(response);
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export function getCurrentUser(accessToken: string): Promise<CurrentUser> {
  return request<CurrentUser>("/auth/me", undefined, accessToken);
}

export function getOrders(accessToken: string): Promise<BackendOrder[]> {
  return request<BackendOrder[]>("/orders", undefined, accessToken);
}

export function getOrdersForReview(
  accessToken: string,
): Promise<BackendReviewOrder[]> {
  return request<BackendReviewOrder[]>("/orders/review", undefined, accessToken);
}

export function markOrderDelivered(
  accessToken: string,
  orderId: string,
): Promise<BackendOrder> {
  return request<BackendOrder>(
    `/orders/${encodeURIComponent(orderId)}/deliver`,
    { method: "POST" },
    accessToken,
  );
}

export function createOrder(
  accessToken: string,
  input: CreateOrderInput,
): Promise<BackendOrder> {
  return request(
    "/orders",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lines: [{ product_id: input.productId, qty: input.quantity }],
        shipping_address: input.shippingAddress,
        card_number: input.cardNumber,
        card_exp: input.cardExp,
        card_cvc: input.cardCvc,
      }),
    },
    accessToken,
  );
}

export function getReturns(accessToken: string): Promise<BackendReturn[]> {
  return request<BackendReturn[]>("/returns", undefined, accessToken);
}

export function getReturnsForReview(
  accessToken: string,
): Promise<BackendReturn[]> {
  return request<BackendReturn[]>("/returns/review", undefined, accessToken);
}

export function getReturn(
  accessToken: string,
  returnId: string,
): Promise<BackendReturn> {
  return request<BackendReturn>(
    `/returns/${encodeURIComponent(returnId)}`,
    undefined,
    accessToken,
  );
}

export function getReturnForReview(
  accessToken: string,
  returnId: string,
): Promise<BackendReturn> {
  return request<BackendReturn>(
    `/returns/review/${encodeURIComponent(returnId)}`,
    undefined,
    accessToken,
  );
}

export function createReturn(
  accessToken: string,
  input: CreateReturnInput,
): Promise<{ id: string; status: string; amount: number | string }> {
  const body = new FormData();
  body.append("order_item_id", input.orderItemId);
  body.append("reason_code", input.reasonCode);
  body.append("reason_text", input.reasonText);
  body.append("photo", input.photo);

  return request("/returns", { method: "POST", body }, accessToken);
}
