# Configuration & Environment Variables

> Last verified against commit: `c39ba3f`

## Environment Variables Dictionary

Configure values in a local `.env` file at the root.

| Variable Name | Required | Consumer | Default / Local Value | Purpose |
|---|---|---|---|---|
| `POSTGRES_USER` | Yes | Postgres, Compose | `postgres` | Database admin username |
| `POSTGRES_PASSWORD` | Yes | Postgres, Compose | `postgres` | Database admin password |
| `POSTGRES_DB` | Yes | Postgres, Compose | `returnguard` | Primary application database |
| `DATABASE_URL` | Yes | Backend, Alembic | `postgresql+asyncpg://postgres:postgres@localhost:5432/returnguard` | AsyncPG connection string for FastAPI & migrations |
| `DATABASE_PSYCOPG_URL` | Yes | Worker | `postgresql://postgres:postgres@localhost:5432/returnguard` | Psycopg connection string for worker direct queries |
| `MINIO_ROOT_USER` | Yes | MinIO, Compose | `minioadmin` | MinIO root administrator |
| `MINIO_ROOT_PASSWORD` | Yes | MinIO, Compose | `minioadmin` | MinIO root password |
| `MINIO_ENDPOINT` | Yes | Backend, Worker | `localhost:9000` | S3 API endpoint for object storage |
| `MINIO_ACCESS_KEY` | Yes | Backend, Worker | `minioadmin` | S3 client access key |
| `MINIO_SECRET_KEY` | Yes | Backend, Worker | `minioadmin` | S3 client secret key |
| `MINIO_BUCKET_NAME` | Yes | Backend, Worker | `returnguard` | Primary bucket for product and return photos |
| `MINIO_SECURE` | No | Backend, Worker | `false` | Whether MinIO endpoint uses HTTPS |
| `KEYCLOAK_ADMIN` | Yes | Keycloak, Compose | `admin` | Keycloak bootstrap administrator |
| `KEYCLOAK_ADMIN_PASSWORD` | Yes | Keycloak, Compose | `admin` | Keycloak bootstrap password |
| `KEYCLOAK_URL` | Yes | Backend | `http://localhost:8081` | Base Keycloak URL for JWKS key discovery |
| `KEYCLOAK_REALM` | Yes | Backend | `returnguard` | Realm containing application clients |
| `KEYCLOAK_CLIENT_ID` | Yes | Backend | `retail-api` | Expected access-token audience |
| `NEXT_PUBLIC_KEYCLOAK_URL` | Yes | Frontend | `http://localhost:8081` | Browser Keycloak login endpoint |
| `NEXT_PUBLIC_KEYCLOAK_REALM` | Yes | Frontend | `returnguard` | Realm for PKCE browser authentication |
| `NEXT_PUBLIC_KEYCLOAK_CLIENT_ID` | Yes | Frontend | `retail-frontend` | Public client for Authorization Code + PKCE |
| `NEXT_PUBLIC_API_URL` | Yes | Frontend | `http://127.0.0.1:8000` | FastAPI base endpoint URL |
| `REDIS_URL` | Yes | Backend, Worker | `redis://localhost:6380/0` | Redis broker for ARQ jobs |
| `QDRANT_URL` | No | Knowledge, Worker | `http://localhost:6333` | Vector database REST endpoint |
| `QDRANT_COLLECTION` | No | Knowledge, Worker | `returnguard_policies` | Target Qdrant collection for policy chunks |
| `GROQ_API_KEY` | As needed | Worker | None | Primary/fallback LLM provider credentials |
| `OPENAI_API_KEY` | As needed | Worker | None | Primary/fallback LLM provider credentials |
| `LANGFUSE_PUBLIC_KEY` | No | Worker | None | Langfuse cloud/local tracing public key |
| `LANGFUSE_SECRET_KEY` | No | Worker | None | Langfuse secret key (tracing enabled if both set) |
