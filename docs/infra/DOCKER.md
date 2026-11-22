# Docker & Infrastructure Specification

> Last verified against commit: `c39ba3f`

## Docker Compose Services (`docker-compose.yml`)

Network: `rg` (bridge driver).

| Service | Image | Ports | Volumes | Healthcheck |
|---|---|---|---|---|
| **`postgres`** | `postgres:18` | `5432:5432` | `pg_data:/var/lib/postgresql`<br>`./infra/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro` | `pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}` |
| **`minio`** | `cgr.dev/chainguard/minio:latest` | `9000:9000`<br>`9001:9001` | `minio_data:/data` | `mc ready local` |
| **`minio-init`** | `cgr.dev/chainguard/minio-client:latest-dev` | None (one-shot) | None | Creates default bucket `returnguard`. |
| **`qdrant`** | `qdrant/qdrant:v1.19.0` | `6333:6333`<br>`6334:6334` | `qdrant_data:/qdrant/storage` | TCP socket probe on `127.0.0.1:6333`. |
| **`keycloak`** | `quay.io/keycloak/keycloak:26.7.2` | `8081:8080`<br>`9002:9000` | `./infra/keycloak/realm-export.json:/opt/keycloak/data/import/realm-export.json:ro` | Built-in Keycloak health check. Connects to Postgres schema `keycloak`. |
| **`redis`** | `redis:7-alpine` | `6380:6379` | `redis_data:/data` | `redis-cli ping` |
| **`mailhog`** | `mailhog/mailhog:v1.0.1` | `1025:1025`<br>`8025:8025` | None | Web interface on 8025; SMTP on 1025. |

## Operations & Makefile Commands
- **Start infrastructure**: `make up` (`docker compose up -d`).
- **Health validation**: `make check` (verifies all running services and one-shot completion).
- **Seed database catalog**: `make seed` (`uv run python seed/seed.py`).
- **Stop containers**: `make stop` (preserves container and volume state).
- **Tear down stack**: `make down` (removes containers and network; retains named volumes).
