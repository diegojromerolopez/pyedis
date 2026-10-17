"""Asyncio TCP server entrypoint and signal handling."""

import asyncio
import os
import signal
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
            commands, buffer = decode_resp_stream(buffer)
            for cmd_args in commands:
                reply, close_conn = await dispatcher.dispatch(cmd_args)
                writer.write(reply)
                await writer.drain()
                if close_conn:
                    return
    except Exception:
        pass
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

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    async with server:
        server_task = asyncio.create_task(server.serve_forever())
        await stop_event.wait()
        server_task.cancel()
        aof.close()
        print("pyedis: shutting down cleanly")


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
