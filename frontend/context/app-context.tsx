"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

import {
  type AppUser,
  type DashboardSummary,
  type Order,
  type Product,
  type RefundRequest,
} from "@/types";
import {
  createProduct as apiCreateProduct,
  getProducts as apiGetProducts,
  mapBackendProductToFrontend,
  checkBackendHealth,
} from "@/lib/shop-api";
import {
  ApiError,
  createOrder as apiCreateOrder,
  createReturn as apiCreateReturn,
  getCurrentUser,
  getOrders,
  getReturns,
  getReturnsForReview,
  getReturnForReview,
  getOrdersForReview,
  markOrderDelivered as apiMarkOrderDelivered,
  type BackendOrder,
  type BackendReviewOrder,
  type BackendReturn,
  type CreateOrderInput,
  type CurrentUser,
} from "@/lib/retail-api";
import {
  clearKeycloakToken,
  endKeycloakSession,
  getCurrentAccessToken,
  initializeKeycloak,
  startKeycloakLogin,
} from "@/lib/keycloak";

export type SubmitRefundRequestInput = {
  orderItemId: string;
  reasonCode: string;
  description: string;
  photo: File;
};

export type ToastState = {
  id: string;
  message: string;
  type: "success" | "info" | "error";
} | null;

interface AppContextValue {
  orders: Order[];
  reviewOrders: BackendReviewOrder[];
  refundRequests: RefundRequest[];
  returnRecords: BackendReturn[];
  products: Product[];
  toast: ToastState;
  summary: DashboardSummary;
  isBackendOnline: boolean | null;
  backendError: string | null;
  accountError: string | null;
  isAuthReady: boolean;
  user: AppUser | null;
  authError: string | null;
  showToast: (message: string, type?: "success" | "info" | "error") => void;
  clearToast: () => void;
  getRefundByOrderItemId: (orderItemId: string) => RefundRequest | undefined;
  getReturnDetails: (returnId: string) => Promise<BackendReturn>;
  markOrderDelivered: (orderId: string) => Promise<{
    success: boolean;
    message: string;
  }>;
  refreshProducts: () => Promise<void>;
  createBackendProduct: (formData: FormData) => Promise<{
    success: boolean;
    message: string;
    product?: Product;
  }>;
  createProductOrder: (
    input: CreateOrderInput,
  ) => Promise<{ success: boolean; message: string; orderId?: string }>;
  signIn: () => Promise<{
    success: boolean;
    message: string;
  }>;
  signOut: () => Promise<void>;
  submitRefundRequest: (input: SubmitRefundRequestInput) => Promise<{
    success: boolean;
    message: string;
    requestId?: string;
  }>;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

function toNumber(value: string | number): number {
  return typeof value === "number" ? value : Number(value);
}

function mapCurrentUser(user: CurrentUser): AppUser {
  return {
    id: user.user_id,
    name: user.name,
    email: user.email,
    role: user.role,
    roles: user.roles,
  };
}

function mapOrders(
  backendOrders: BackendOrder[],
  user: AppUser,
  returns: BackendReturn[],
): Order[] {
  const returnByItem = new Map<string, BackendReturn>();
  for (const item of returns) {
    if (!returnByItem.has(item.order_item_id)) {
      returnByItem.set(item.order_item_id, item);
    }
  }

  return backendOrders.flatMap((backendOrder) =>
    backendOrder.items.map((item) => {
      const returnRequest = returnByItem.get(item.id);
      const returnStatus = returnRequest?.status.toLowerCase();
      const refundStatus =
        returnStatus === "approved"
          ? "Approved"
          : returnStatus === "refunded"
            ? "Refunded"
          : returnStatus === "denied" || returnStatus === "rejected"
            ? "Denied"
            : returnRequest
              ? "Pending Review"
              : "Not Requested";
      const unitPrice = toNumber(item.unit_price);

      return {
        id: backendOrder.id,
        orderItemId: item.id,
        customer: user,
        product: {
          id: item.product_id,
          name: item.name,
          category: "Purchased item",
          price: unitPrice,
          image: "",
          tone: "bg-[#E8E1D9] text-[#483F3D]",
        },
        orderDate: backendOrder.placed_at,
        quantity: item.qty,
        unitPrice,
        totalPrice: unitPrice * item.qty,
        orderStatus: backendOrder.status,
        refundStatus,
        paymentLast4: backendOrder.payment_last4,
        orderTotal: toNumber(backendOrder.total),
      };
    }),
  );
}

const reasonLabels: Record<string, string> = {
  damaged: "Damaged",
  not_as_described: "Not as described",
  wrong_item: "Wrong item",
  no_longer_needed: "No longer needed",
  defective: "Defective",
  arrived_late: "Arrived late",
  quality: "Quality issue",
};

function mapReturns(
  backendReturns: BackendReturn[],
  orders: Order[],
  user: AppUser,
): RefundRequest[] {
  const orderByItem = new Map(orders.map((order) => [order.orderItemId, order]));

  return backendReturns.map((item) => {
    const order = orderByItem.get(item.order_item_id);
    const status = item.status.toLowerCase();
    const reviewStatus =
      status === "approved"
        ? "Approved"
        : status === "refunded"
          ? "Refunded"
        : status === "denied" || status === "rejected"
          ? "Denied"
          : "Pending Review";

    return {
      id: item.id,
      orderId: item.order_id,
      orderItemId: item.order_item_id,
      customer: user,
      product: order?.product ?? {
        id: item.order_item_id,
        name: "Purchased item",
        category: "Purchased item",
        price: toNumber(item.amount),
        image: "",
        tone: "bg-[#E8E1D9] text-[#483F3D]",
      },
      requestedAmount: toNumber(item.amount),
      orderAmount: order?.orderTotal ?? toNumber(item.amount),
      orderDate: order?.orderDate ?? item.created_at,
      quantity: order?.quantity ?? 1,
      reason: reasonLabels[item.reason_code] ?? item.reason_code,
      description: item.reason_text,
      submissionDate: item.created_at,
      reviewStatus,
      // agent_results is the structured pipeline data used by the reviewer page.
      // The customer-facing refunds page doesn't need it, so aiProposedDecision
      // is set to null here (it was previously derived from ai_proposed_decision
      // which no longer exists on the API response).
      aiProposedDecision: null,
      finalDecision: item.final_decision,
      photoUrls: item.photo_urls,
    };
  });
}

export function AppProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [reviewOrders, setReviewOrders] = useState<BackendReviewOrder[]>([]);
  const [refundRequests, setRefundRequests] = useState<RefundRequest[]>([]);
  const [returnRecords, setReturnRecords] = useState<BackendReturn[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [isBackendOnline, setIsBackendOnline] = useState<boolean | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [accountError, setAccountError] = useState<string | null>(null);
  const [isAuthReady, setIsAuthReady] = useState(false);
  const [user, setUser] = useState<AppUser | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastState>(null);

  const showToast = useCallback(
    (message: string, type: "success" | "info" | "error" = "success") => {
      setToast({ id: String(Date.now()), message, type });
      window.setTimeout(() => {
        setToast((current) => (current?.message === message ? null : current));
      }, 3500);
    },
    [],
  );

  const clearToast = useCallback(() => {
    setToast(null);
  }, []);

  const clearAuthState = useCallback((message: string | null) => {
    clearKeycloakToken();
    setAccessToken(null);
    setUser(null);
    setOrders([]);
    setReviewOrders([]);
    setRefundRequests([]);
    setReturnRecords([]);
    setAuthError(message);
  }, []);

  const loadAccountData = useCallback(
    async (token: string, account: AppUser) => {
      try {
        const isCustomer = account.roles.includes("customer");
        const canReview = account.roles.some(
          (role) => role === "admin" || role === "reviewer",
        );
        const [backendOrders, customerReturns, reviewReturns, ordersForReview] =
          await Promise.all([
            isCustomer ? getOrders(token) : Promise.resolve([]),
            isCustomer ? getReturns(token) : Promise.resolve([]),
            canReview ? getReturnsForReview(token) : Promise.resolve([]),
            canReview ? getOrdersForReview(token) : Promise.resolve([]),
          ]);
        const mappedOrders = mapOrders(backendOrders, account, customerReturns);
        setOrders(mappedOrders);
        setReviewOrders(ordersForReview);
        setReturnRecords(canReview ? reviewReturns : customerReturns);
        setRefundRequests(
          mapReturns(customerReturns, mappedOrders, account),
        );
        setAccountError(null);
      } catch (error: unknown) {
        const message =
          error instanceof Error ? error.message : "Could not load account data.";
        if (error instanceof ApiError && error.status === 401) {
          clearAuthState("Your API session has expired. Please sign in again.");
          return;
        }
        setAccountError(message);
        showToast(message, "error");
      }
    },
    [clearAuthState, showToast],
  );

  const refreshProducts = useCallback(async () => {
    const health = await checkBackendHealth();
    setIsBackendOnline(health.online);
    if (!health.online) {
      const message = health.details || "FastAPI backend is offline.";
      setBackendError(message);
      setProducts([]);
      return;
    }

    const response = await apiGetProducts({ limit: 100 });
    if (!response.success) {
      setBackendError(response.error || "Failed to load products from the API.");
      setProducts([]);
      return;
    }

    setProducts(response.data.map(mapBackendProductToFrontend));
    setBackendError(null);
  }, []);

  useEffect(() => {
    let ignore = false;
    void (async () => {
      try {
        const health = await checkBackendHealth();
        if (ignore) return;
        setIsBackendOnline(health.online);
        if (!health.online) {
          setBackendError(health.details || "FastAPI backend is offline.");
          setProducts([]);
          return;
        }

        const response = await apiGetProducts({ limit: 100 });
        if (ignore) return;
        if (!response.success) {
          setBackendError(
            response.error || "Failed to load products from the API.",
          );
          setProducts([]);
          return;
        }
        setProducts(response.data.map(mapBackendProductToFrontend));
        setBackendError(null);
      } catch (error: unknown) {
        if (ignore) return;
        setBackendError(
          error instanceof Error ? error.message : "Could not load products.",
        );
        setIsBackendOnline(false);
        setProducts([]);
      }
    })();

    void (async () => {
      try {
        const authenticated = await initializeKeycloak();
        if (!authenticated) return;

        const token = await getCurrentAccessToken();
        if (!token) throw new Error("Keycloak did not return an access token.");

        const currentUser = mapCurrentUser(await getCurrentUser(token));
        if (ignore) return;
        setAccessToken(token);
        setUser(currentUser);
        const landingPage =
          currentUser.role === "reviewer" || currentUser.role === "admin"
            ? "/returns"
            : "/dashboard";
        if (window.location.pathname !== landingPage) {
          router.replace(landingPage);
        }
        await loadAccountData(token, currentUser);
      } catch (error: unknown) {
        if (ignore) return;
        clearAuthState(
          error instanceof Error
            ? error.message
            : "Could not initialize Keycloak authentication.",
        );
      } finally {
        if (!ignore) setIsAuthReady(true);
      }
    })();

    return () => {
      ignore = true;
    };
  }, [clearAuthState, loadAccountData, refreshProducts, router]);

  const createBackendProduct = useCallback(
    async (formData: FormData) => {
      const response = await apiCreateProduct(formData);
      if (!response.success || !response.data) {
        const message = response.error || "Failed to create product.";
        showToast(message, "error");
        return { success: false, message };
      }

      const product = mapBackendProductToFrontend(response.data, products.length);
      setProducts((current) => [product, ...current]);
      showToast(`Product "${product.name}" created successfully.`);
      return {
        success: true,
        message: `Product "${product.name}" created successfully.`,
        product,
      };
    },
    [products.length, showToast],
  );

  const createProductOrder = useCallback(
    async (input: CreateOrderInput) => {
      if (!accessToken) {
        return { success: false, message: "Please sign in to place an order." };
      }
      if (!user?.roles.includes("customer")) {
        return {
          success: false,
          message: "Only customer accounts can place an order.",
        };
      }

      try {
        const order = await apiCreateOrder(accessToken, input);
        await Promise.all([
          loadAccountData(accessToken, user),
          refreshProducts(),
        ]);
        showToast(`Order ${order.id} placed successfully.`);
        return {
          success: true,
          message: `Order ${order.id} placed successfully.`,
          orderId: order.id,
        };
      } catch (error: unknown) {
        const message =
          error instanceof Error ? error.message : "Failed to place the order.";
        if (error instanceof ApiError && error.status === 401) {
          clearAuthState("Your API session has expired. Please sign in again.");
        }
        showToast(message, "error");
        return { success: false, message };
      }
    },
    [
      accessToken,
      clearAuthState,
      loadAccountData,
      refreshProducts,
      showToast,
      user,
    ],
  );

  const signIn = useCallback(
    async () => {
      try {
        await startKeycloakLogin();
        return { success: true, message: "Redirecting to Keycloak." };
      } catch (error: unknown) {
        const message = error instanceof Error ? error.message : "Could not sign in.";
        setAuthError(message);
        return { success: false, message };
      }
    },
    [],
  );

  const signOut = useCallback(async () => {
    let logoutError: string | null = null;
    try {
      await endKeycloakSession();
    } catch (error: unknown) {
      logoutError =
        error instanceof Error ? error.message : "Could not end Keycloak session.";
    }
    clearAuthState(logoutError);
    if (logoutError) showToast(logoutError, "error");
  }, [clearAuthState, showToast]);

  const getRefundByOrderItemId = useCallback(
    (orderItemId: string) =>
      refundRequests.find((request) => request.orderItemId === orderItemId),
    [refundRequests],
  );

  const getReturnDetails = useCallback(
    async (returnId: string) => {
      if (!accessToken) {
        throw new ApiError("Please sign in to view return details.");
      }
      try {
        return await getReturnForReview(accessToken, returnId);
      } catch (error: unknown) {
        if (error instanceof ApiError && error.status === 401) {
          clearAuthState("Your API session has expired. Please sign in again.");
        }
        throw error;
      }
    },
    [accessToken, clearAuthState],
  );

  const markOrderDelivered = useCallback(
    async (orderId: string) => {
      if (!accessToken) {
        return { success: false, message: "Please sign in to update orders." };
      }
      if (
        !user?.roles.some((role) => role === "admin" || role === "reviewer")
      ) {
        return {
          success: false,
          message: "Only administrators and reviewers can update orders.",
        };
      }

      try {
        await apiMarkOrderDelivered(accessToken, orderId);
        setReviewOrders((current) =>
          current.filter((order) => order.id !== orderId),
        );
        showToast(`Order ${orderId} marked as delivered.`);
        return { success: true, message: `Order ${orderId} marked as delivered.` };
      } catch (error: unknown) {
        const message =
          error instanceof Error ? error.message : "Could not update the order.";
        if (error instanceof ApiError && error.status === 401) {
          clearAuthState("Your API session has expired. Please sign in again.");
        }
        showToast(message, "error");
        return { success: false, message };
      }
    },
    [accessToken, clearAuthState, showToast, user],
  );

  const submitRefundRequest = useCallback(
    async ({
      orderItemId,
      reasonCode,
      description,
      photo,
    }: SubmitRefundRequestInput) => {
      if (!accessToken) {
        return { success: false, message: "Please sign in to submit a return." };
      }
      if (!user?.roles.includes("customer")) {
        return {
          success: false,
          message: "Only customer accounts can submit a return.",
        };
      }
      if (!orders.some((order) => order.orderItemId === orderItemId)) {
        return { success: false, message: "Order item not found." };
      }
      if (!photo) {
        return { success: false, message: "A supporting photo is required." };
      }

      try {
        const result = await apiCreateReturn(accessToken, {
          orderItemId,
          reasonCode,
          reasonText: description.trim(),
          photo,
        });
        if (user) await loadAccountData(accessToken, user);
        showToast(`Return request ${result.id} submitted successfully.`);
        return {
          success: true,
          message: `Return request ${result.id} submitted successfully.`,
          requestId: result.id,
        };
      } catch (error: unknown) {
        const message =
          error instanceof Error ? error.message : "Failed to submit return.";
        if (error instanceof ApiError && error.status === 401) {
          clearAuthState("Your API session has expired. Please sign in again.");
        }
        showToast(message, "error");
        return { success: false, message };
      }
    },
    [accessToken, clearAuthState, loadAccountData, orders, showToast, user],
  );

  const summary = useMemo<DashboardSummary>(() => {
    const uniqueOrders = new Map<string, number>();
    for (const order of orders) {
      uniqueOrders.set(order.id, order.orderTotal);
    }
    return {
      totalOrders: uniqueOrders.size,
      totalSpending: [...uniqueOrders.values()].reduce(
        (total, amount) => total + amount,
        0,
      ),
      pendingRefundRequests: refundRequests.filter(
        (request) => request.reviewStatus === "Pending Review",
      ).length,
      completedRefunds: refundRequests.filter(
        (request) => request.reviewStatus !== "Pending Review",
      ).length,
    };
  }, [orders, refundRequests]);

  const value = useMemo<AppContextValue>(
    () => ({
      orders,
      reviewOrders,
      refundRequests,
      returnRecords,
      products,
      toast,
      summary,
      isBackendOnline,
      backendError,
      accountError,
      isAuthReady,
      user,
      authError,
      showToast,
      clearToast,
      getRefundByOrderItemId,
      getReturnDetails,
      markOrderDelivered,
      refreshProducts,
      createBackendProduct,
      createProductOrder,
      signIn,
      signOut,
      submitRefundRequest,
    }),
    [
      orders,
      reviewOrders,
      refundRequests,
      returnRecords,
      products,
      toast,
      summary,
      isBackendOnline,
      backendError,
      accountError,
      isAuthReady,
      user,
      authError,
      showToast,
      clearToast,
      getRefundByOrderItemId,
      getReturnDetails,
      markOrderDelivered,
      refreshProducts,
      createBackendProduct,
      createProductOrder,
      signIn,
      signOut,
      submitRefundRequest,
    ],
  );

  if (!isAuthReady) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-[#77746E]">
        Connecting to your account...
      </div>
    );
  }

  return (
    <AppContext.Provider value={value}>
      {user ? children : <SignInScreen />}
    </AppContext.Provider>
  );
}

function SignInScreen() {
  const context = useContext(AppContext);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!context) {
    throw new Error("SignInScreen must be rendered inside AppProvider");
  }

  const handleSignIn = async () => {
    setError("");
    setIsSubmitting(true);
    const result = await context.signIn();
    setIsSubmitting(false);
    if (!result.success) setError(result.message);
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F8F7F4] px-4 py-10">
      <section className="w-full max-w-md rounded-3xl border border-[#E8E6E1] bg-white p-8 shadow-sm">
        <div className="mb-7">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#777D65]">
            Marlow Commerce
          </p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-[#252525]">
            Sign in to your account
          </h1>
          <p className="mt-2 text-sm text-[#77746E]">
            Your orders and return requests are loaded securely from the API.
          </p>
        </div>

        <div className="space-y-4">
          {(error || context.authError) && (
            <p role="alert" className="rounded-xl bg-[#FBEBE8] p-3 text-sm text-[#783D31]">
              {error || context.authError}
            </p>
          )}
          <button
            type="button"
            onClick={() => void handleSignIn()}
            disabled={isSubmitting}
            className="w-full rounded-xl bg-[#777D65] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#656B55] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Redirecting..." : "Continue with Keycloak"}
          </button>
        </div>
      </section>
    </main>
  );
}

export function useAppData() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppData must be used within an AppProvider");
  }
  return context;
}
