# Backend API Specification

> Last verified against commit: `c39ba3f`

## Overview
FastAPI service mounted at `backend/main.py`. Base URL: `http://localhost:8000`. Interactive docs: `/docs`.

## Global Endpoints

| Method | Endpoint | Access | Handler | Description |
|---|---|---|---|---|
| `GET` | `/health` | Public | `backend/main.py:health` | Database connection health check (`request.app.state.db.health_check()`). Returns `{"ok": true}`. |

## Shop & Catalog Routes (`backend/app/router/shop.py`)

| Method | Endpoint | Access | Handler | Request / Response Shape |
|---|---|---|---|---|
| `GET` | `/products` | Public | `list_products` | Query: `category` (str), `limit` (int, default 50), `offset` (int, default 0). Returns `list[ProductOut]`. Presigns MinIO image URLs. |
| `GET` | `/products/{product_id}` | Public | `get_product` | Path: UUID `product_id`. Returns `ProductOut`. 404 if missing. |
| `POST` | `/products` | Admin/Reviewer | `create_product` | Multipart form: `name`, `description`, `category`, `price`, `stock`, `image` (file: JPEG/PNG/WebP, max 5MB). Uploads to MinIO, returns `ProductOut` (201). |

## Order Routes (`backend/app/router/order.py`)

| Method | Endpoint | Access | Handler | Request / Response Shape |
|---|---|---|---|---|
| `POST` | `/orders` | Customer | `create_order` | Body: `OrderCreateIn` (`items`, `shipping_address`, `card_last4`). Header: `Idempotency-Key`. Deducts stock, creates Order + OrderItems, sends confirmation via MailHog, returns `OrderOut`. |
| `GET` | `/orders` | Customer | `my_orders` | Returns `list[OrderOut]` for authenticated user, newest first. Includes items and presigned product image URLs. |
| `GET` | `/orders/review` | Reviewer/Admin | `review_orders` | Query: `status` (default `pending`), `limit` (int), `offset` (int). Returns `list[OrderOut]` with customer email. |
| `POST` | `/orders/{order_id}/delivered` | Reviewer/Admin | `mark_delivered` | Path: int `order_id`. Sets status to `delivered` and `delivered_at = now()`. Returns `OrderOut`. |

## Return Routes (`backend/app/router/returns.py`)

| Method | Endpoint | Access | Handler | Request / Response Shape |
|---|---|---|---|---|
| `POST` | `/returns` | Customer | `submit_return` | Multipart form: `order_item_id` (int), `reason_code` (enum), `reason_text` (str), `photo` (file, required for damage/quality). Creates Return, ReturnPhoto, Outbox row, dispatches ARQ `review_return`, sends receipt email. Returns `ReturnCreateOut`. |
| `GET` | `/returns` | Customer | `my_returns` | Returns `list[ReturnOut]` for authenticated customer with photo URLs. |
| `GET` | `/returns/review` | Reviewer/Admin | `review_returns` | Returns `list[ReturnOut]` across all customers, ordered by `created_at desc`. |
| `GET` | `/returns/review/{return_id}` | Reviewer/Admin | `get_return_for_review` | Returns single `ReturnOut` including presigned photos. 404 if not found. |
| `GET` | `/returns/{return_id}` | Customer | `get_return` | Returns single `ReturnOut` belonging to authenticated customer. |

## Identity Routes (`backend/app/router/auth.py`)

| Method | Endpoint | Access | Handler | Request / Response Shape |
|---|---|---|---|---|
| `GET` | `/auth/me` | Authenticated | `me` | Returns `UserOut` (`id`, `keycloak_sub`, `name`, `email`, `role`). Auto-provisions user row. |

## Reason Codes & Statuses (`backend/app/models.py`)
- **Return Statuses**: `pending`, `in_review`, `escalated`, `approved`, `denied`, `refunded`.
- **Reason Codes**: `damaged`, `not_as_described`, `quality`, `wrong_item`, `no_longer_needed`, `defective`, `arrived_late`, `wrong_size`, `item_not_received`, `duplicate_item`, `accidental_order`.
- **Photo Required Codes**: `damaged`, `defective`, `wrong_item`, `quality`, `not_as_described`.
