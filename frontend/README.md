# Retail Refund Governance Frontend

This folder contains the web interface for the retail order, product, and refund
management experience. It is built with Next.js App Router, React, TypeScript,
Tailwind CSS, and Lucide icons.

The interface reads products from the FastAPI backend and uses the authenticated
orders and returns endpoints for account data. Sign in with an API account to
view orders or submit a return request with the required evidence photo. If the
backend is unavailable, the UI shows an error rather than substituting demo data.

## Run and validate

Run these commands from this folder:

```bash
npm install
npm run dev
```

The app is then available at [http://localhost:3000](http://localhost:3000), or
at the alternate port printed by Next.js if port 3000 is already in use.

## Local Keycloak development accounts

These are the seeded **local development** accounts:

| Role | Email / username | Password |
|---|---|---|
| Customer | `customer1@gmail.com` | `customer123` |
| Reviewer | `reviewer1@returnguard.local` | `reviewer1` |
| Reviewer | `reviewer2@returnguard.local` | `reviewer2` |
| Admin | `admin1@returnguard.local` | `admin1` |

These credentials are for local development only. Do not use them in
production.

```bash
npm run lint
npm run build
```

## Routes

| Route | File | Purpose |
|---|---|---|
| `/` | `app/page.tsx` | Redirects to the dashboard. |
| `/dashboard` | `app/dashboard/page.tsx` | Shows account order and return summary statistics and recent activity. |
| `/orders` | `app/orders/page.tsx` | Lets customers find orders, inspect order details, and submit return requests. |
| `/order-review` | `app/order-review/page.tsx` | Lets administrators and reviewers inspect pending orders and mark them delivered. |
| `/refunds` | `app/refunds/page.tsx` | Shows return history and API decision details. |
| `/products` | `app/products/page.tsx` | Displays the product catalog and supports product details and product creation. |

All authenticated pages share the application shell, account header, and
notification toast for local action feedback.

## Folder and file guide

### `app/` — routes and global presentation

- `app/layout.tsx` — Root document layout, page metadata, Geist fonts, global
  stylesheet, and the `AppProvider` that makes shared app state available.
- `app/globals.css` — Tailwind import, warm-neutral theme variables, global
  typography, and base element styling.
- `app/page.tsx` — Root-route redirect to `/dashboard`.
- `app/dashboard/page.tsx` — Dashboard route, including the computed summary
  cards and recent order/refund activity.
- `app/orders/page.tsx` — Order search and filtering, order details state, and
  refund-request dialog state.
- `app/order-review/page.tsx` — Reviewer/admin pending-order queue and delivery
  confirmation flow.
- `app/refunds/page.tsx` — Account return history, status filtering, and request
  details from the API.
- `app/products/page.tsx` — Product catalog search/filtering and state for
  product details and creation.
- `app/favicon.ico` — Browser tab icon.

### `components/` — reusable interface pieces

- `components/app-shell.tsx` — Shared page frame; composes the sidebar and
  header, renders page content, and displays app-wide toast messages.
- `components/layout/Sidebar.tsx` — Main navigation links and mobile sidebar
  behavior.
- `components/layout/Header.tsx` — Page heading, mobile menu control, and
  authenticated account details/sign-out.
- `components/dashboard/RecentActivity.tsx` — Recent orders and refund activity
  on the dashboard, with links and detail views.
- `components/orders/OrdersTable.tsx` — Orders table, status badges, and
  row-level detail/return actions.
- `components/orders/OrderDetails.tsx` — Order detail modal content.
- `components/orders/RefundRequestDialog.tsx` — Customer return form and its
  input validation UI.
- `components/products/ProductCard.tsx` — Single product card in the catalog.
- `components/products/ProductDetailsModal.tsx` — Product information modal.
- `components/products/CreateProductModal.tsx` — Product creation form,
  including image selection.
- `components/refunds/RefundsTable.tsx` — Account return history table.
- `components/refunds/RefundDetails.tsx` — Return details, evidence links, and
  API decision information.
- `components/ui/Badge.tsx` — Shared status badge using the common status
  styles.
- `components/ui/Button.tsx` — Shared button variants and styling.
- `components/ui/ConfirmationModal.tsx` — Reusable confirmation dialog for
  consequential actions.
- `components/ui/DataTable.tsx` — Shared table layout and empty-state
  presentation.
- `components/ui/Modal.tsx` — Base modal with close and keyboard/focus behavior.
- `components/ui/StatCard.tsx` — Dashboard summary-statistic card.

### `context/` — shared client-side application state

- `context/app-context.tsx` — Defines `AppProvider` and `useAppData`. It handles
  sign-in, loads account data from FastAPI, calculates dashboard totals, submits
  returns, and loads or creates products.

### `lib/` — data, API, and formatting helpers

- `lib/shop-api.ts` — FastAPI product API calls, backend health check, and
  mapping from backend product responses to the frontend product shape.
- `lib/retail-api.ts` — FastAPI current-user, customer/reviewer order, and return
  requests.
- `lib/keycloak.ts` — Browser-based Keycloak login and access-token management
  using Authorization Code flow with PKCE.
- `lib/utils.ts` — Shared class-name composition, money/date formatting, and
  status-to-style mappings.

### `types/` — shared TypeScript contracts

- `types/index.ts` — Shared interfaces and unions for accounts, products,
  orders, returns, dashboard summary data, and backend product responses.

### `public/` — static assets

- `public/file.svg`, `public/globe.svg`, `public/next.svg`,
  `public/vercel.svg`, and `public/window.svg` — Static SVG assets available
  from the site root. They are starter assets and can be removed if unused.

### Root configuration files

- `package.json` — Project scripts and direct dependencies.
- `package-lock.json` — Exact npm dependency resolution for repeatable installs.
- `next.config.ts` — Next.js settings, allowed remote image hosts, and the
  `/api/backend/:path*` rewrite to the FastAPI service.
- `tsconfig.json` — TypeScript settings, strict checking, and the `@/*` import
  alias for this folder.
- `eslint.config.mjs` — ESLint configuration for Next.js and TypeScript.
- `next-env.d.ts` — Next.js-generated TypeScript declarations; do not edit
  manually.
- `.gitignore` — Files and generated output excluded from version control.
- `AGENTS.md` — Next.js-generated agent guidance for this installed Next.js
  version; it is not part of the application runtime.

## FastAPI product-catalog configuration

`lib/shop-api.ts` and `lib/retail-api.ts` use `NEXT_PUBLIC_API_URL` as the API
base URL and default to `http://127.0.0.1:8000`. `next.config.ts` uses
`BACKEND_URL` for the
`/api/backend/:path*` rewrite, falling back to `NEXT_PUBLIC_API_URL` and then
`http://127.0.0.1:8000`.

The context checks backend health when the app loads and fetches the live
product catalog. Sign-in is handled by Keycloak in the browser using
Authorization Code flow with PKCE; the frontend refreshes access tokens through
the Keycloak client and sends them to protected FastAPI endpoints. Return
submissions use the API's supported reason codes and must include a JPEG, PNG,
or WebP evidence photo. The current backend exposes no reviewer approve/reject
action, so the returns page displays the status and decision fields returned by
the service without offering simulated decisions.
