from __future__ import annotations

import asyncio
import os
from contextlib import suppress

import uvicorn
from loguru import logger

from .config import load_config
from .discord_runner import run_bots
from .logging_setup import setup_logging


async def _main_async() -> int:
    cfg = load_config()
    setup_logging(cfg.logging.level)

    # Start HTTP server if metrics or health desired
    port = cfg.runtime.metrics_port or cfg.runtime.health_port
    server_task = None
    if port:
        config = uvicorn.Config("talkative.http_server:app", host="0.0.0.0", port=port, log_level="info")
        server = uvicorn.Server(config)
        server_task = asyncio.create_task(server.serve())

    await run_bots(cfg)

    if server_task:
        server_task.cancel()
        with suppress(asyncio.CancelledError):
            await server_task
    return 0


def main() -> None:
    try:
        asyncio.run(_main_async())
    except KeyboardInterrupt:
        logger.info("Shutting down")


if __name__ == "__main__":
    main()
