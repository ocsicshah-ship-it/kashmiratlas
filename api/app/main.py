"""FastAPI application entry point."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import close_pool, open_pool
from .routers import cells, hexes, places


@asynccontextmanager
async def lifespan(app: FastAPI):
    await open_pool()
    yield
    await close_pool()


app = FastAPI(
    title="Kashmir Valley Capability Atlas API",
    version="0.1.0",
    lifespan=lifespan,
)

_origins = [
    o.strip()
    for o in os.environ.get("API_CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(cells.router, prefix="/api")
app.include_router(places.router, prefix="/api")
app.include_router(hexes.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Serve the designed single-page atlas (web/index.html) same-origin, so its
# fetch('/api/...') calls need no CORS. Mounted last so /api and /health win.
_web_dir = os.environ.get("ATLAS_WEB_DIR") or str(Path(__file__).resolve().parents[2] / "web")
if Path(_web_dir).is_dir():
    app.mount("/", StaticFiles(directory=_web_dir, html=True), name="web")
