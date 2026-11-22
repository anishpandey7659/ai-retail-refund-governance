# Backend Authentication & Security

> Last verified against commit: `c39ba3f`

## Overview
Identity and access management is powered by Keycloak (realm `returnguard`). The FastAPI backend statelessly validates OpenID Connect RS256 Bearer tokens and synchronizes user profiles.

## Flow & Components (`backend/app/security/auth.py`)

```text
Browser Client
     |
     | 1. Authorize with PKCE (port 8081)
     v
Keycloak 26 (/realms/returnguard)
     |
     | 2. Returns Access Token (RS256 JWT)
     v
FastAPI Request Header: "Authorization: Bearer <token>"
     |
     | 3. Fetch/Verify Signing Key via JWKS
     v
backend/app/security/auth.py (_jwks() -> PyJWKClient)
     |
     | 4. Validate claims: exp, iss, sub, aud
     v
Database User Provisioning / Role Check
```

## Token Verification Details
- **JWKS Client**: `PyJWKClient` instantiated against `KEYCLOAK_URL/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs`. Public keys cached for 1 hour (`_jwks_at`).
- **Algorithms**: RS256 only.
- **Audience (`aud`)**: Checked against `get_settings().keycloak_client_id` (`retail-api`).
- **Issuer (`iss`)**: Checked against `get_settings().keycloak_issuer` (`http://localhost:8081/realms/returnguard`).

## Role Extraction & Permissions
Keycloak assigns roles in `realm_access.roles`:
- **`admin`**: Full access to catalog creation, all customer orders, and all returns.
- **`reviewer`**: Access to `/orders/review`, `/returns/review`, and delivery marking.
- **`customer`**: Default role; restricted to personal orders (`/orders`) and personal returns (`/returns`).

### Role Guard Helpers:
- `require_role(*allowed_roles)`: FastAPI dependency that decodes token claims, verifies role membership, and loads the active `User` model.
- Auto-provisioning: If the user does not exist in `users` table on first valid request, `get_current_user` creates the user record (`keycloak_sub`, `name`, `email`, `role`). If name or email changed in Keycloak, the DB record is updated.

## Keycloak Local Test Accounts (`frontend/README.md`)
- `customer1@gmail.com` / `customer123` (Role: `customer`)
- `reviewer1@returnguard.local` / `reviewer1` (Role: `reviewer`)
- `reviewer2@returnguard.local` / `reviewer2` (Role: `reviewer`)
- `admin1@returnguard.local` / `admin1` (Role: `admin`)
