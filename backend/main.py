from fastapi import  FastAPI, Request,Depends
from backend.dependency import lifespan

from backend.app.router import order_router,shop_router,auth_router,return_router


app = FastAPI(lifespan=lifespan)
app.include_router(shop_router)
app.include_router(order_router)
app.include_router(auth_router)
app.include_router(return_router)

@app.get("/health")
async def health(request: Request):
    return {"ok": await request.app.state.db.health_check()}




# uv run uvicorn backend.main:app --reload