"""FastAPI application — Upstream People backend."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routes import game, analysis

app = FastAPI(
    title="Upstream People",
    description="PLO poker engine API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game.router, prefix="/game", tags=["game"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])


@app.get("/health")
async def health():
    return {"status": "ok", "engine": "plo_engine"}
