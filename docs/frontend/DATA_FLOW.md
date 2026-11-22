# Frontend Data Flow & API Integration

> Last verified against commit: `c39ba3f`

## Overview
The frontend communicates with the FastAPI backend and Keycloak identity provider using client-side React Context (`frontend/context/app-context.tsx`) and typed API service clients (`frontend/lib/`).

```text
Browser Client
  ├── Keycloak Auth (frontend/lib/keycloak.ts)
  │     └── In-memory access token + automatic token refresh
  │
  ├── AppContext (frontend/context/app-context.tsx)
  │     ├── Stores: products, orders, returns, metrics, user session
  │     └── Exposes: refreshCatalog, submitReturn, markDelivered, createProduct
  │
  └── API Clients (frontend/lib/)
        ├── shop-api.ts   ---> Next.js Proxy / Rewrite ---> FastAPI (/products)
        └── retail-api.ts ---> Bearer Token Request   ---> FastAPI (/orders, /returns)
```

## API Clients & Contract Mapping

### 1. Catalog Client (`frontend/lib/shop-api.ts`)
- Target: FastAPI `/products` endpoints.
- Fallback: Integrates local catalog fallback (`seed/products.json`) if backend is unreachable.
- Operations:
  - `getProducts({ category, limit, offset })`: Fetches catalog with presigned MinIO `image_url` links.
  - `getProductById(id)`: Fetches single product details.
  - `createProduct(formData)`: Sends `multipart/form-data` with product attributes and photo.
  - `checkBackendHealth()`: Probes `GET /health` with a 3-second timeout.

### 2. Retail & Return Client (`frontend/lib/retail-api.ts`)
- Target: Protected FastAPI endpoints using Bearer token authentication.
- Operations:
  - `getCurrentUser()`: Calls `GET /auth/me` to retrieve backend user record and role.
  - `getOrders()` / `getReviewOrders()`: Fetches customer orders or reviewer queue.
  - `getReturns()` / `getReviewReturns()`: Fetches customer return history or reviewer claims.
  - `submitReturn(formData)`: Posts multipart form (`order_item_id`, `reason_code`, `reason_text`, `photo`) to `POST /returns`.

### 3. Next.js Proxies & Rewrites (`frontend/next.config.ts`)
- Rewrites: `/api/backend/:path*` is proxied to `BACKEND_URL` (default `http://127.0.0.1:8000/:path*`).
- Remote Image Patterns: Configured for `images.unsplash.com`, `localhost:9000`, and `127.0.0.1:9000` (MinIO S3 storage).
