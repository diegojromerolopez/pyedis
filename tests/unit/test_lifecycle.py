import asyncio
import subprocess
import sys
import unittest

from src.main import lifecycle
from src.server import Server


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_server_starts_accepts_and_stops_deterministically(self) -> None:
        server = Server(port=0)
        address = await server.start()
        self.assertEqual(address[0], "127.0.0.1")
        self.assertGreater(address[1], 0)
        reader, writer = await asyncio.open_connection(*address)
        writer.close()
        await writer.wait_closed()
        await server.stop()
        with self.assertRaises(RuntimeError):
            _ = server.address

    async def test_entrypoint_lifecycle_is_cancellable(self) -> None:
        task = asyncio.create_task(lifecycle())
        await asyncio.sleep(0)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task


class ModuleEntrypointTests(unittest.TestCase):
    def test_module_entrypoint_reports_operational_errors(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "src.main"],
            env={**__import__("os").environ, "PORT": "not-a-port"},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("pyedis: "))


if __name__ == "__main__":
    unittest.main()
