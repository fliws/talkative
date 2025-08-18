from __future__ import annotations

import asyncio
from typing import Optional

import orjson
from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse


app = FastAPI()


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    return {"status": "ready"}


@app.get("/metrics")
async def metrics():
    data = generate_latest()  # default registry
    return PlainTextResponse(data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


def run_http_server(port: int) -> asyncio.AbstractServer:
    # We'll start uvicorn programmatically in run.py; this file only defines the app
    raise NotImplementedError
