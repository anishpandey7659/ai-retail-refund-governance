# Backend Database Specification

> Last verified against commit: `c39ba3f`

## Database Architecture
- **Engine**: PostgreSQL 18 on port 5432 (database: `returnguard`).
- **Connection URL**: `postgresql+asyncpg://` via `PostgreSQLSettings.database_url` (`backend/app/config.py`).
- **Initialization**: Automatically invokes `Base.metadata.create_all` during FastAPI startup lifespan (`backend/dependency.py`, `backend/app/services/storage.py`).
- **Migrations**: Managed by Alembic (`backend/alembic.ini`, `backend/alembic/env.py`). Version scripts located in `backend/alembic/versions/`.

## Core Entities & Relationships (`backend/app/models.py`)

### 1. Identity
- **`users`**: Primary customer/staff table.
  - Columns: `id` (UUID PK), `keycloak_sub` (unique index), `name`, `email` (unique), `role` (`customer`, `reviewer`, `admin`), `created_at`, `updated_at`.
- **`reviewers`**: Staff extension.
  - Columns: `id` (UUID PK), `user_id` (FK `users.id` cascade, unique), `name`.

### 2. Shop & Catalog
- **`products`**: Sellable inventory items.
  - Columns: `id` (UUID PK), `name` (unique), `description`, `category` (indexed), `price` (Numeric 10,2), `stock` (Integer), `image_key` (MinIO key).
- **`orders`**: Customer purchase transactions.
  - Columns: `id` (Integer PK), `user_id` (FK `users.id`), `total_amount` (Numeric 10,2), `shipping_address`, `card_last4`, `payment_method_fingerprint`, `status` (indexed), `delivered_at`.
- **`order_items`**: Line items within an order.
  - Columns: `id` (Integer PK), `order_id` (FK `orders.id`), `product_id` (FK `products.id`), `quantity`, `price_at_purchase`, `name_at_purchase`.
- **`order_address_changes`**: Historical shipping address changes prior to or after delivery.
  - Columns: `id` (UUID PK), `order_id` (FK `orders.id`), `changed_at`.

### 3. Returns & Refunds
- **`returns`**: Return claims and adjudication state.
  - Columns: `id` (UUID PK), `user_id` (FK `users.id`), `order_id` (FK `orders.id`), `order_item_id` (FK `order_items.id`), `reason_code`, `reason_text`, `amount`, `status`, `ai_result` (JSONB), `review_attempts`, `claimed_by` (FK `users.id`), `decided_by` (FK `users.id`), `item_received`, `item_opened`, `inspected_by`, `inspected_at`.
  - Unique Constraint: `uq_open_return_per_item` ensures only one active (non-finalized) return per order item.
- **`return_photos`**: Uploaded evidence images.
  - Columns: `id` (UUID PK), `return_id` (FK `returns.id` cascade), `object_key`, `content_type`, `bytes`, `sha256`.
- **`return_refunds`**: Monetary disbursement records.
  - Columns: `id` (UUID PK), `return_id` (FK `returns.id`), `amount`, `status` (`pending`, `succeeded`, `failed`), `provider_refund_id`, `destination_fingerprint` (String 64), `error`, `created_at`, `processed_at`.
  - Unique Constraint: `uq_one_success_refund` prevents double refunds on a single return.

### 4. Risk & Infrastructure
- **`support_contacts`**: Customer support volume tracking.
- **`fingerprints`**: Device, card, and address hashes (`uq_fingerprint_per_user`).
- **`outbox`**: Transactional outbox table (`event_type`, `payload` JSONB, `status`, `attempts`).
- **`review_queue`**: Direct table written by worker when cases require human review (`order_id`, `decision`, `explanation`, `payload` JSONB, `status`).

## Audit Trigger [Implemented]
- `audit_log_append_only`: Function `forbid_audit_change()` installed by `backend/app/services/storage.py` blocks UPDATE and DELETE operations on `audit_log`.
