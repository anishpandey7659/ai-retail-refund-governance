from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependency import get_db_session
from backend.app.models import Reviewer, User
from backend.app.config import get_settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logging.getLogger("backend").setLevel(logging.INFO)
log = logging.getLogger(__name__)

# Gives Swagger its Authorize button and reads "Authorization: Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

_jwks_client: jwt.PyJWKClient | None = None
_jwks_at = 0.0


def _jwks() -> jwt.PyJWKClient:
    global _jwks_client, _jwks_at
    if _jwks_client is None or time.time() - _jwks_at > 3600:
        _jwks_client = jwt.PyJWKClient(get_settings().keycloak_jwks_url)
        _jwks_at = time.time()
    return _jwks_client


@dataclass
class Principal:
    sub: str
    email: str
    name: str
    roles: list[str] = field(default_factory=list)
    user_id: str = ""
    reviewer_id: str | None = None

    def has(self, role: str) -> bool:
        return role in self.roles


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _decode(token: str) -> dict:
    """Validate a Keycloak JWT and return its claims."""
    s = get_settings()
    try:
        key = _jwks().get_signing_key_from_jwt(token).key
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=s.keycloak_issuer,
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("token expired") from None
    except jwt.InvalidIssuerError:
        try:
            iss = jwt.decode(token, options={"verify_signature": False}).get("iss")
        except jwt.PyJWTError:
            iss = "?"
        log.warning("issuer mismatch: token=%s expected=%s", iss, s.keycloak_issuer)
        raise _unauthorized("invalid issuer") from None
    except jwt.PyJWKClientConnectionError:
        # Keycloak unreachable: a server-side problem, not a bad token
        log.exception("cannot reach JWKS at %s", s.keycloak_jwks_url)
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "auth service unavailable"
        ) from None
    except jwt.PyJWTError as e:
        log.warning("token rejected: %s", e)
        raise _unauthorized(f"invalid token: {e}") from e


async def get_principal(
    token: str ,
    session: AsyncSession = Depends(get_db_session),
) -> Principal:
    if not token:
        log.info("auth: no bearer token on request")
        raise _unauthorized("missing bearer token")
        

    claims = _decode(token)

    sub = claims.get("sub")
    if not sub:
        raise _unauthorized("token has no subject")

    email = claims.get("email") or claims.get("preferred_username") or f"{sub}@no-email"
    name = claims.get("name") or claims.get("preferred_username") or email
    roles = list(claims.get("realm_access", {}).get("roles", []))
    app_roles = [r for r in roles if r in ("customer", "reviewer", "admin")]
    role = "admin" if "admin" in app_roles else "reviewer" if "reviewer" in app_roles else "customer"

    try:
        user = (
            await session.execute(select(User).where(User.keycloak_sub == sub))
        ).scalar_one_or_none()

        if user is None:
            user = User(keycloak_sub=sub, email=email, name=name, role=role)
            session.add(user)
            await session.flush()
            if role in ("reviewer", "admin"):
                session.add(Reviewer(user_id=user.id, name=name))
            await session.commit()
            log.info("user.created sub=%s role=%s", sub, role)
        elif user.role != role or user.email != email or user.name != name:
            user.role, user.email, user.name = role, email, name
            await session.commit()

        reviewer = (
            await session.execute(select(Reviewer).where(Reviewer.user_id == user.id))
        ).scalar_one_or_none()

    except IntegrityError:
        # Two first requests raced to create the same user; reload and continue
        await session.rollback()
        user = (
            await session.execute(select(User).where(User.keycloak_sub == sub))
        ).scalar_one()
        reviewer = (
            await session.execute(select(Reviewer).where(Reviewer.user_id == user.id))
        ).scalar_one_or_none()
    except Exception:
        await session.rollback()
        log.exception("failed to load or create user for sub=%s", sub)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "could not load user") from None

    return Principal(
        sub=sub, email=email, name=name, roles=app_roles,
        user_id=str(user.id), reviewer_id=str(reviewer.id) if reviewer else None,
    )


async def current_user(p: Principal = Depends(get_principal)) -> Principal:
    return p


def require_role(*allowed: str):
    async def _dep(p: Principal = Depends(get_principal)) -> Principal:
        if not any(p.has(r) for r in allowed):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"requires one of {allowed}")
        return p

    return _dep