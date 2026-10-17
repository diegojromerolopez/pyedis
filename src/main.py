"""Asyncio TCP server entrypoint."""

import asyncio

from src.server import run_from_environment


def main() -> None:
    try:
        asyncio.run(run_from_environment())
    except KeyboardInterrupt:
        print("pyedis: shutting down gracefully")


if __name__ == "__main__":
    main()
