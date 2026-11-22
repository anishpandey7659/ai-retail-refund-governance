from __future__ import annotations

import logging
import time

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.models import Reviewer, User
from backend.dependency import get_db_session

log = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)

_jwks_client: jwt.PyJWKClient | None = None
_jwks_at = 0.0


def _jwks() -> jwt.PyJWKClient:
    global _jwks_client, _jwks_at
    if _jwks_client is None or time.time() - _jwks_at > 3600:
        _jwks_client = jwt.PyJWKClient(
            get_settings().keycloak_jwks_url,
            cache_keys=True,
        )
        _jwks_at = time.time()
    return _jwks_client


def _unauthorized(detail: str = "invalid or expired access token") -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _decode(token: str) -> dict:
    """Verify a Keycloak access token and return its claims."""
    settings = get_settings()
    try:
        key = _jwks().get_signing_key_from_jwt(token).key
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.keycloak_client_id,
            issuer=settings.keycloak_issuer,
            options={"require": ["exp", "iss", "sub", "aud"]},
        )
    except jwt.PyJWKClientConnectionError as exc:
        log.exception("Unable to retrieve Keycloak signing keys")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "authentication service unavailable",
        ) from exc
    except jwt.PyJWKClientError as exc:
        log.info("Could not find a Keycloak signing key for the token")
        raise _unauthorized() from exc
    except jwt.PyJWTError as exc:
        log.info("Rejected Keycloak access token: %s", exc)
        raise _unauthorized() from exc


def _role_from_claims(claims: dict) -> str:
    realm_access = claims.get("realm_access")
    realm_roles = realm_access.get("roles", []) if isinstance(realm_access, dict) else []
    roles = set(realm_roles) if isinstance(realm_roles, list) else set()
    if "admin" in roles:
        return "admin"
    if "reviewer" in roles:
        return "reviewer"
    return "customer"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    if credentials is None:
        raise _unauthorized("missing bearer token")

    claims = _decode(credentials.credentials)
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub:
        raise _unauthorized("token has no subject")

    preferred_username = claims.get("preferred_username")
    email = claims.get("email") or preferred_username or f"{sub}@no-email"
    name = claims.get("name") or preferred_username or email
    role = _role_from_claims(claims)

    user = (
        await session.execute(select(User).where(User.keycloak_sub == sub))
    ).scalar_one_or_none()
    try:
        is_new_user = user is None
        if is_new_user:
            user = User(
                keycloak_sub=sub,
                email=email,
                name=name,
                role=role,
            )
            session.add(user)

        changed = is_new_user
        if is_new_user:
            await session.flush()

        if user.email != email:
            user.email = email
            changed = True
        if user.name != name:
            user.name = name
            changed = True
        if user.role != role:
            user.role = role
            changed = True

        if role in ("reviewer", "admin"):
            reviewer = (
                await session.execute(
                    select(Reviewer).where(Reviewer.user_id == user.id)
                )
            ).scalar_one_or_none()
            if reviewer is None:
                session.add(Reviewer(user_id=user.id, name=name))
                changed = True
            elif reviewer.name != name:
                reviewer.name = name
                changed = True

        if changed:
            await session.flush()
            await session.commit()
        return user
    except IntegrityError as exc:
        await session.rollback()
        # Another request may have provisioned this subject while this one
        # was inserting. Do not bind a different subject through email alone.
        user = (
            await session.execute(select(User).where(User.keycloak_sub == sub))
        ).scalar_one_or_none()
        if user is not None:
            return user
        log.info("User provisioning conflicted for subject %s", sub)
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "account conflicts with an existing user",
        ) from exc


def require_role(*allowed_roles: str):
    async def role_dependency(
        user: User = Depends(get_current_user),
    ) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "insufficient permissions",
            )
        return user

    return role_dependency


async def promote_to_reviewer(
    user: User,
    session: AsyncSession,
) -> Reviewer:
    user.role = "reviewer"
    reviewer = (
        await session.execute(select(Reviewer).where(Reviewer.user_id == user.id))
    ).scalar_one_or_none()
    if reviewer is None:
        reviewer = Reviewer(user_id=user.id, name=user.name)
        session.add(reviewer)
    await session.flush()
    return reviewer
