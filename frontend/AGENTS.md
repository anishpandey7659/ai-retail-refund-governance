# Frontend Agent Guide

## Responsibilities & Stack
- **Scope**: Next.js 16 App Router interface for shopping, orders, return requests, and review dashboards.
- **Stack**: Next.js 16, React 19, TypeScript, Tailwind CSS v4, `keycloak-js`, `lucide-react`.

## Key Directories & Entry Points
- `frontend/app/`: App Router pages (`/dashboard`, `/orders`, `/order-review`, `/refunds`, `/products`).
- `frontend/components/`: Modular UI widgets (`frontend/components/ui/`, `frontend/components/layout/`, feature dialogs).
- `frontend/context/app-context.tsx`: Shared state management (`AppProvider`, `useAppData`).
- `frontend/lib/`: `shop-api.ts` (catalog), `retail-api.ts` (orders/returns), `keycloak.ts` (PKCE auth).
- `frontend/types/`: Shared TypeScript data definitions (`frontend/types/index.ts`).

## Conventions & Rules
- Access FastAPI through `frontend/lib/shop-api.ts` and `frontend/lib/retail-api.ts` using Next rewrites (`/api/backend/:path*`).
- Manage client authentication state through Keycloak PKCE; attach Bearer token to API calls.
- Return submissions require a photo and valid reason code (`damaged`, `defective`, etc.).
- Run lint and build checks before finishing tasks.

## Testing & Execution
- Run dev server: `npm run dev` (Port 3000).
- Lint and typecheck: `npm run lint`.
- Build production bundle: `npm run build`.

## Docs to Read
- `docs/frontend/OVERVIEW.md`, `docs/frontend/DATA_FLOW.md`, `docs/backend/API.md`.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
