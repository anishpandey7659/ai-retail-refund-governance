from fastapi import APIRouter, Depends

from backend.app.models import User
from backend.app.security.auth import get_current_user

auth_router = APIRouter(tags=["auth"])


@auth_router.get("/me")
@auth_router.get("/auth/me")
async def me(user: User = Depends(get_current_user)) -> dict:
    return {
        "user_id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "roles": [user.role],
    }
