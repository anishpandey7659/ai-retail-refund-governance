# Architectural Decision Records (ADRs)

> Last verified against commit: `c39ba3f`

## ADR 001: Separation of Database Access Layers
- **Status:** [Implemented]
- **Context:** The FastAPI backend and ARQ worker have different runtime lifecycles and query profiles. The API performs complex relational object mapping, while the worker executes high-throughput read-heavy aggregation queries for feature extraction.
- **Decision:** Use SQLAlchemy 2.0 with `asyncpg` in `backend/` for domain models and REST transactions. Use raw SQL parameterized queries with `psycopg 3` connection pool (`psycopg_pool.AsyncConnectionPool`) in `worker/pipeline/`.
- **Consequences:** Avoids ORM overhead and session conflicts in background workers; requires maintaining raw SQL queries (`RETURN_QUERY`, `ML_CONTEXT_QUERY`) in `worker/pipeline/query.py`.

## ADR 002: Fail-Safe Kill Switch & Human Review Queue
- **Status:** [Implemented]
- **Context:** Automated AI agent decisions must never issue irreversible refunds or unmonitored rejections without safeguards.
- **Decision:** Implement a fail-safe `human_review_kill_switch` in `worker/pipeline/helper.py`. When active (or defaulted to None), every evaluated case is routed into the `review_queue` table as `pending` with full JSONB case telemetry.
- **Consequences:** AI acts strictly as an advisory system producing proposals, leaving final monetary disbursement to human reviewers.

## ADR 003: Keycloak PKCE & Backend JWKS Verification
- **Status:** [Implemented]
- **Context:** Need standard OpenID Connect authentication supporting role-based access control (`customer`, `reviewer`, `admin`) across web and API.
- **Decision:** Use OAuth 2.0 Authorization Code Flow with PKCE in the frontend (`keycloak-js`). Backend validates RS256 signatures statelessly via Keycloak JWKS endpoint (`PyJWKClient` with 1-hour cache).
- **Consequences:** Eliminates shared client secrets in browser; backend independently auto-provisions and syncs user rows upon first verified token receipt.

## ADR 004: Multi-Modal Return Verification Pipeline
- **Status:** [Implemented]
- **Context:** Fraudulent return prevention requires assessing photographic evidence plausibility alongside customer behavioral history.
- **Decision:** Combine deterministic data-quality gates, CLIP image similarity (`openai/clip-vit-base-patch32`), an AI-generated image classifier (`haywoodsloan/ai-image-detector-deploy`), EXIF metadata checks, and a vision LLM fallback for borderline cases.
- **Consequences:** Fast local screening handles obvious matches/mismatches with zero external LLM API cost, calling vision models only when ambiguity exists.

## ADR 005: Hybrid Dense + Sparse BM25 Policy Retrieval
- **Status:** [Implemented]
- **Context:** Refund policies contain precise legal numbers (e.g., "14 days", "unopened") and conceptual eligibility rules. Pure semantic vector search frequently misses exact numeric thresholds.
- **Decision:** Use Qdrant hybrid search combining dense vectors (`BAAI/bge-small-en-v1.5` or OpenAI `text-embedding-3-small`) with sparse BM25 vectors (`Qdrant/bm25`), fused using Reciprocal Rank Fusion (RRF).
- **Consequences:** Yields high precision for exact policy clauses and high recall for conversational customer queries.

## ADR 006: Local Transactional Email via MailHog
- **Status:** [Implemented]
- **Context:** Need transactional emails for order confirmations and return acknowledgments in development without external SMTP dependencies.
- **Decision:** Route all emails to containerized MailHog on port 1025. Failure to connect to MailHog logs a warning but never breaks customer requests.
- **Consequences:** Zero external API keys needed for email; developers can inspect outbound messages at `http://localhost:8025`.
