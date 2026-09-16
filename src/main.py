"""Executable entry point for the asyncio TCP server."""

from __future__ import annotations

import asyncio

from .server import run_server


def main() -> None:
    asyncio.run(run_server())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
