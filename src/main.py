"""Thin entrypoint wrapper - delegates to src.server.run_server."""

from __future__ import annotations

import asyncio
import sys

from src.server import run_server

if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        sys.exit(0)
