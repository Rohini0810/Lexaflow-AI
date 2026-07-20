from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import actions, admin, dashboard, health, monitor, regulations, sources, versions
from backend.app.core.config import settings
from backend.app.db.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version="2.0.0", lifespan=lifespan)

# Ensure local DB exists even when startup events are not fired (e.g. some test clients).
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root() -> dict:
    return {"name": settings.app_name, "status": "running"}


app.include_router(health.router)
app.include_router(actions.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)
app.include_router(monitor.router, prefix=settings.api_prefix)
app.include_router(regulations.router, prefix=settings.api_prefix)
app.include_router(sources.router, prefix=settings.api_prefix)
app.include_router(versions.router, prefix=settings.api_prefix)


