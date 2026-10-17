"""Asyncio TCP server entrypoint and signal handlers."""

import asyncio
import os
import sys
from src.commands import CommandDispatcher
from src.persistence import AOFLogger, replay_aof
from src.resp import decode_resp_stream
from src.store import Store


async def handle_client(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, dispatcher: CommandDispatcher
) -> None:
    buffer = bytearray()
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            buffer.extend(data)
            cmds, remaining = decode_resp_stream(buffer)
            buffer = remaining
            for cmd in cmds:
                resp, should_close = await dispatcher.dispatch(cmd)
                writer.write(resp)
                await writer.drain()
                if should_close:
                    return
    except Exception as e:
        print(f"pyedis: connection error {e}", file=sys.stderr)
    finally:
        writer.close()
        await writer.wait_closed()


async def run_server(
    host: str = "0.0.0.0", port: int = 6379, data_dir: str = "./data", fsync: bool = True
) -> None:
    os.makedirs(data_dir, exist_ok=True)
    aof_path = os.path.join(data_dir, "dump.aof")
    store = Store()
    replay_aof(aof_path, store)
    aof = AOFLogger(aof_path, fsync=fsync)
    dispatcher = CommandDispatcher(store, aof)
    server = await asyncio.start_server(lambda r, w: handle_client(r, w, dispatcher), host, port)
    print(f"pyedis: listening on {host}:{port}")
    try:
        await server.serve_forever()
    finally:
        server.close()
        await server.wait_closed()


def main() -> None:
    port = int(os.environ.get("PORT", 6379))
    data_dir = os.environ.get("PYEDIS_DATA_DIR", "./data")
    fsync = os.environ.get("PYEDIS_AOF_FSYNC", "true").lower() == "true"
    try:
        asyncio.run(run_server(port=port, data_dir=data_dir, fsync=fsync))
    except KeyboardInterrupt:
        print("pyedis: shutting down gracefully")


if __name__ == "__main__":
    main()
