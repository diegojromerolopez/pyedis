import asyncio
import sys
from typing import Optional

from src.commands import CommandDispatcher
from src.resp import parse_command
from src.store import Store


async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    dispatcher: CommandDispatcher,
) -> None:
    buffer = b""
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            buffer += data
            while True:
                cmd_args, remaining = parse_command(buffer)
                if cmd_args is None:
                    break
                buffer = remaining
                if cmd_args:
                    response = await dispatcher.dispatch(cmd_args)
                    writer.write(response)
                    await writer.drain()
    except (asyncio.CancelledError, ConnectionResetError):
        pass
    finally:
        writer.close()
        await writer.wait_closed()


async def run_server(
    host: str = "0.0.0.0", port: int = 6379, store: Optional[Store] = None
) -> None:
    if store is None:
        store = Store()
    dispatcher = CommandDispatcher(store)

    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, dispatcher),
        host,
        port,
    )
    sys.stderr.write(f"pyedis: server listening on {host}:{port}\n")
    sys.stderr.flush()

    async with server:
        await server.serve_forever()


def main() -> None:
    sys.stderr.write("pyedis: starting server...\n")
    sys.stderr.flush()
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
