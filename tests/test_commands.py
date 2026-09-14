import tempfile
import unittest
from src.commands import Dispatcher
from src.persistence import AOF
from src.store import Store

class CommandTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.dispatcher = Dispatcher(Store(), AOF(self.temp.name + "/dump.aof", False))

    async def asyncTearDown(self) -> None:
        self.temp.cleanup()

    async def test_set_get_and_errors(self) -> None:
        self.assertEqual(await self.dispatcher.dispatch([b"set", b"a", b"1"]), b"+OK\r\n")
        self.assertEqual(await self.dispatcher.dispatch([b"GET", b"a"]), b"$1\r\n1\r\n")
        self.assertTrue((await self.dispatcher.dispatch([b"missing"])).startswith(b"-ERR unknown command"))

if __name__ == "__main__":
    unittest.main()
