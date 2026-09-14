import asyncio
import os
import signal
import sys
from src.commands import CommandDispatcher
from src.persistence import AOFLogger
from src.resp import RESPDecoder
from src.store import Store


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, dispatcher: CommandDispatcher) -> None:
    decoder = RESPDecoder()
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            decoder.feed(data)
            cmds = decoder.decode_multi()
            for cmd_args in cmds:
                response, should_close = await dispatcher.dispatch(cmd_args)
                if response:
                    writer.write(response)
                    await writer.drain()
                if should_close:
                    writer.close()
                    await writer.wait_closed()
                    return
    except Exception as e:
        sys.stderr.write(f"pyedis: error handling client: {e}\n")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def run_server() -> None:
    port = int(os.environ.get("PORT", "6379"))
    data_dir = os.environ.get("PYEDIS_DATA_DIR", "./data")
    fsync = os.environ.get("PYEDIS_AOF_FSYNC", "true").lower() == "true"

    try:
        store = Store()
        aof = AOFLogger(data_dir, fsync=fsync)
        aof.replay(store)
        dispatcher = CommandDispatcher(store, aof)
    except Exception as e:
        sys.stderr.write(f"pyedis: fatal startup error: {e}\n")
        sys.exit(1)

    server = await asyncio.start_server(lambda r, w: handle_client(r, w, dispatcher), "0.0.0.0", port)
    sys.stdout.write(f"pyedis: server listening on port {port}\n")
    sys.stdout.flush()

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    async with server:
        server_task = asyncio.create_task(server.serve_forever())
        await stop_event.wait()
        server.close()
        await server.wait_closed()
        server_task.cancel()
        sys.stdout.write("pyedis: server shutdown cleanly\n")


def main() -> None:
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
