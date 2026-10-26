from fastapi import  FastAPI, Request
from backend.dependency import lifespan

from backend.app.router.shop import router


app = FastAPI(lifespan=lifespan)
app.include_router(router)

@app.get("/health")
async def health(request: Request):
    return {"ok": await request.app.state.db.health_check()}



# uv run uvicorn backend.main:app --reload