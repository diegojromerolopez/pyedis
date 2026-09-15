import asyncio
import unittest
from src.resp import Decoder

class ServerTest(unittest.IsolatedAsyncioTestCase):
    async def test_decoder_handles_pipelining(self) -> None:
        decoder = Decoder(); frames = decoder.feed(b'*1\r\n$4\r\nPING\r\n*1\r\n$4\r\nQUIT\r\n')
        self.assertEqual(len(frames), 2)
