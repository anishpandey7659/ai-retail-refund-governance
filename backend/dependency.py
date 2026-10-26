from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from backend.app.services.storage import PostgreSQLDatabase
from backend.app.config import PostgreSQLSettings

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = PostgreSQLDatabase(PostgreSQLSettings())
    await db.startup()
    app.state.db = db
    yield
    await db.teardown()


async def get_db_session(request: Request):
    async with request.app.state.db.get_session() as session:
        yield session
