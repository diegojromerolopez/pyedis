"""Async TCP Server for pyedis."""

import asyncio
import os
import sys
import signal
from typing import Optional

from src.resp import parse_resp_command
from src.commands import handle_command


def log_info(msg: str) -> None:
    print(f"pyedis: {msg}", file=sys.stdout, flush=True)


def log_error(msg: str) -> None:
    print(f"pyedis: {msg}", file=sys.stderr, flush=True)


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    addr = writer.get_extra_info("peername")
    log_info(f"Client connected from {addr}")
    try:
        while True:
            args = await parse_resp_command(reader)
            if args is None:
                # Connection closed by client
                break
            if not args:
                continue

            response, should_close = handle_command(args)
            if response:
                writer.write(response)
                await writer.drain()

            if should_close:
                break
    except (asyncio.IncompleteReadError, ConnectionResetError):
        pass
    except Exception as e:
        log_error(f"Error handling client {addr}: {e}")
    finally:
        log_info(f"Client disconnected from {addr}")
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


async def main() -> None:
    port_env = os.getenv("PORT", "6379")
    try:
        port = int(port_env)
    except ValueError:
        log_error(f"Invalid PORT environment variable: '{port_env}'")
        sys.exit(1)

    try:
        server = await asyncio.start_server(handle_client, "0.0.0.0", port)
    except Exception as e:
        log_error(f"Failed to start server on port {port}: {e}")
        sys.exit(1)

    log_info(f"Server started on port {port}")

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def shutdown_signal():
        log_info("Received shutdown signal, stopping server...")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown_signal)
        except NotImplementedError:
            pass

    async with server:
        server_task = asyncio.create_task(server.serve_forever())
        stop_task = asyncio.create_task(stop_event.wait())
        done, pending = await asyncio.wait(
            [server_task, stop_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    log_info("Server shut down cleanly")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SystemExit as e:
        sys.exit(e.code)
    except KeyboardInterrupt:
        log_info("KeyboardInterrupt received, exiting")
        sys.exit(0)
    except Exception as e:
        log_error(f"Fatal error: {e}")
        sys.exit(1)
