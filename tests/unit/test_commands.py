import unittest
from src.commands import Dispatcher
from src.resp import error
from src.store import Store


class CommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_set_get_and_case(self) -> None:
        d = Dispatcher(Store())
        reply, _ = await d.dispatch([b"sEt", b"k", b"v"])
        self.assertEqual(reply, b"+OK\r\n")
        reply, _ = await d.dispatch([b"GET", b"k"])
        self.assertEqual(reply, b"$1\r\nv\r\n")

    async def test_unknown(self) -> None:
        reply, _ = await Dispatcher(Store()).dispatch([b"NOPE"])
        self.assertEqual(reply, error("ERR unknown command 'NOPE'"))
