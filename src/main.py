"""Executable entry point for the asyncio TCP server."""

from __future__ import annotations

import asyncio

from .server import run_server


async def lifecycle() -> None:
    """Run the server lifecycle until cancellation or an operating-system signal."""
    await run_server()


def main() -> None:
    try:
        asyncio.run(lifecycle())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
