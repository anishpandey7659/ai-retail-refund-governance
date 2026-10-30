# backend/app/routers/auth.py
import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from backend.app.config import get_settings
from backend.app.security.auth import Principal, current_user   # adjust to your module path

auth_router = APIRouter(prefix="/auth", tags=["auth"])


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


def _oidc(path: str) -> str:
    return f"{get_settings().keycloak_issuer}/protocol/openid-connect/{path}"



def _client_creds() -> dict:
    s = get_settings()
    data = {"client_id": s.keycloak_client_id}
    if getattr(s, "keycloak_client_secret", None):
        data["client_secret"] = s.keycloak_client_secret
    return data


async def _post(path: str, data: dict) -> httpx.Response:
    async with httpx.AsyncClient(timeout=10) as client:
        return await client.post(_oidc(path), data={**_client_creds(), **data})


@auth_router.post("/login", response_model=TokenOut)
async def login(form: OAuth2PasswordRequestForm = Depends()) -> TokenOut:
    r = await _post("token", {
        "grant_type": "password",
        "username": form.username,
        "password": form.password,
        "scope": "openid",
    })
    if r.status_code != 200:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid username or password")
    return TokenOut(**{k: r.json()[k] for k in TokenOut.model_fields if k in r.json()})


@auth_router.post("/refresh", response_model=TokenOut)
async def refresh(refresh_token: str = Form(...)) -> TokenOut:
    r = await _post("token", {"grant_type": "refresh_token", "refresh_token": refresh_token})
    if r.status_code != 200:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh token invalid or expired")
    return TokenOut(**{k: r.json()[k] for k in TokenOut.model_fields if k in r.json()})


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(refresh_token: str = Form(...)) -> None:
    # Ends the Keycloak session and invalidates the refresh token
    await _post("logout", {"refresh_token": refresh_token})


from fastapi import Header
@auth_router.get("/me")
async def me(
    p: Principal = Depends(current_user),
):
    return {"email": p.email, "name": p.name, "roles": p.roles, "user_id": p.user_id}