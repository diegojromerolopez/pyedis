"""Command-line entrypoint for the asyncio TCP server."""

import asyncio
import os
import sys

from src.server import run_server


def main() -> None:
    port = int(os.getenv("PORT", "6379"))
    data_dir = os.getenv("PYEDIS_DATA_DIR", "./data")
    fsync = os.getenv("PYEDIS_AOF_FSYNC", "true").lower() == "true"
    try:
        asyncio.run(run_server(port=port, data_dir=data_dir, fsync=fsync))
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
