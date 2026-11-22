# Frontend Architecture & UI Overview

> Last verified against commit: `c39ba3f`

## Technology Stack
- **Framework**: Next.js 16 (App Router with Turbopack), React 19.
- **Styling**: Tailwind CSS v4, `@tailwindcss/turbopack`, warm-neutral CSS theme in `frontend/app/globals.css`.
- **Icons**: `lucide-react`.
- **Identity**: `keycloak-js` (PKCE client).

## Route Hierarchy (`frontend/app/`)

| Route | Page File | Purpose |
|---|---|---|
| `/` | `frontend/app/page.tsx` | Permanent redirect to `/dashboard`. |
| `/dashboard` | `frontend/app/dashboard/page.tsx` | Summary KPI cards (total orders, returns, pending rate) and recent activity widgets. |
| `/orders` | `frontend/app/orders/page.tsx` | Customer order list, search, order detail modal, and refund request submission dialog. |
| `/order-review` | `frontend/app/order-review/page.tsx` | Reviewer and administrator pending order review and delivery confirmation queue. |
| `/refunds` | `frontend/app/refunds/page.tsx` | Return claims history, status filter, and API decision rationale inspection. |
| `/products` | `frontend/app/products/page.tsx` | Shop catalog with category filter, product details modal, and multipart product creation form. |

## Component Directory (`frontend/components/`)
- **Shell**: `frontend/components/app-shell.tsx` wraps every authenticated route with responsive desktop sidebar, mobile navigation drawer, and application toast feedback.
- **Layout**: `frontend/components/layout/Sidebar.tsx` (navigation tabs with badges), `frontend/components/layout/Header.tsx` (breadcrumbs, user profile, Keycloak sign-out).
- **Dashboard**: `frontend/components/dashboard/RecentActivity.tsx` (recent orders table and return claims feed).
- **Orders**: `frontend/components/orders/OrdersTable.tsx` (tabular orders), `frontend/components/orders/OrderDetails.tsx` (modal), `frontend/components/orders/RefundRequestDialog.tsx` (customer return submission form with image file validation).
- **Products**: `frontend/components/products/ProductCard.tsx`, `frontend/components/products/ProductDetailsModal.tsx`, `frontend/components/products/CreateProductModal.tsx` (multipart form with image preview).
- **Refunds**: `frontend/components/refunds/RefundsTable.tsx` (claims overview), `frontend/components/refunds/RefundDetails.tsx` (claims inspection with decision metadata).
- **Shared UI**: `frontend/components/ui/Badge.tsx`, `frontend/components/ui/Button.tsx`, `frontend/components/ui/Modal.tsx`, `frontend/components/ui/ConfirmationModal.tsx`, `frontend/components/ui/DataTable.tsx`, `frontend/components/ui/StatCard.tsx`.

## Key Commands
- Run development server: `npm run dev` (Port 3000).
- Typecheck and lint: `npm run lint`.
- Production build: `npm run build`.
