export type OrderStatus = string;

export type RefundStatus =
  | "Not Requested"
  | "Pending Review"
  | "Approved"
  | "Denied"
  | "Refunded";

export type ReviewStatus = "Pending Review" | "Approved" | "Denied" | "Refunded";

export interface Customer {
  id: string;
  name: string;
  email: string;
}

export interface Product {
  id: string;
  name: string;
  category: string;
  price: number;
  image: string;
  tone: string;
  description?: string;
  stock?: number;
  image_url?: string;
}

export interface BackendProductOut {
  id: string;
  name: string;
  description: string;
  category: string;
  price: number;
  stock: number;
  image_url: string;
}

export interface CreateProductInput {
  name: string;
  description: string;
  category: string;
  price: number;
  stock: number;
  image: File;
}

export interface Order {
  id: string;
  orderItemId: string;
  customer: Customer;
  product: Product;
  orderDate: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
  orderStatus: OrderStatus;
  refundStatus: RefundStatus;
  paymentLast4: string;
  orderTotal: number;
}

export interface RefundRequest {
  id: string;
  orderId: string;
  orderItemId: string;
  customer: Customer;
  product: Product;
  requestedAmount: number;
  orderAmount: number;
  orderDate: string;
  quantity: number;
  reason: string;
  description: string;
  submissionDate: string;
  reviewStatus: ReviewStatus;
  aiProposedDecision: string | null;
  finalDecision: string | null;
  photoUrls: string[];
}

export interface DashboardSummary {
  totalOrders: number;
  totalSpending: number;
  pendingRefundRequests: number;
  completedRefunds: number;
}

export interface AppUser {
  id: string;
  name: string;
  email: string;
  role: string;
  roles: string[];
}
