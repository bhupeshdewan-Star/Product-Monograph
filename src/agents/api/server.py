from __future__ import annotations

import logging
import os
import time
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

logging.basicConfig(
    level=os.getenv("GLOBAL_AGENTS_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(
    title="Global Agents Service",
    description="Provider-agnostic accessibility and checklist-driven audit agents",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_metadata_middleware(request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{(time.perf_counter() - started) * 1000:.2f}"
    return response

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "global-agents"}


@app.get("/")
def root():
    return {
        "service": "global-agents",
        "endpoints": [
            "/agents/a11y/check",
            "/agents/auditor/build",
            "/agents/auditor/run",
            "/agents/auditor/build-and-run",
            "/agents/cache/stats",
            "/agents/cache/clear",
            "/agents/ratelimit/status",
            "/agents/auditor/registry",
            "/agents/auditor/history",
        ],
    }
