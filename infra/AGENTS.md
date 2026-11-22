# Infrastructure Agent Guide

## Responsibilities & Stack
- **Scope**: Local container stack orchestration, database schema bootstrap, and Keycloak realm setup.
- **Stack**: Docker, Docker Compose, PostgreSQL 18, MinIO, Qdrant, Keycloak 26, Redis 7, MailHog.

## Key Directories & Entry Points
- `docker-compose.yml`: Core service definitions, network (`rg`), and persistent volumes.
- `infra/postgres/init.sql`: Creates `returnguard` database and `keycloak` schema.
- `infra/keycloak/realm-export.json`: Keycloak realm import configuration.
- `Makefile`: Target shortcuts (`make up`, `make check`, `make stop`, `make down`, `make seed`).

## Conventions & Rules
- Always verify running containers with `make check` before starting API or worker processes.
- Keep credentials out of tracked files; configure local parameters in `.env`.
- Any Keycloak configuration changes made in the admin UI must be exported back to `infra/keycloak/realm-export.json`.
- Do not remove named volumes unless performing a complete environment reset.

## Operations
- Start stack: `make up` (`docker compose up -d`).
- Stop stack: `make stop`.
- Inspect email: `http://localhost:8025` (MailHog).
- Inspect MinIO: `http://localhost:9001` (Credentials in `.env`).

## Docs to Read
- `docs/infra/DOCKER.md`, `docs/infra/CONFIGURATION.md`.
