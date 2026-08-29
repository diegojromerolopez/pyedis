import asyncio
import socket
import threading
import unittest
from src.main import handle_client
from src.commands import handle_command


class TestCommandRouter(unittest.TestCase):
    """Unit tests for command routing in src/commands.py."""

    def test_ping_no_args(self):
        res, close = handle_command(["PING"])
        self.assertEqual(res, b"+PONG\r\n")
        self.assertFalse(close)

    def test_ping_case_insensitive(self):
        res, close = handle_command(["pInG"])
        self.assertEqual(res, b"+PONG\r\n")
        self.assertFalse(close)

    def test_ping_with_arg(self):
        res, close = handle_command(["PING", "hello"])
        self.assertEqual(res, b"$5\r\nhello\r\n")
        self.assertFalse(close)

    def test_ping_too_many_args(self):
        res, close = handle_command(["PING", "hello", "world"])
        self.assertTrue(res.startswith(b"-ERR"))
        self.assertFalse(close)

    def test_echo_valid(self):
        res, close = handle_command(["ECHO", "hello world"])
        self.assertEqual(res, b"$11\r\nhello world\r\n")
        self.assertFalse(close)

    def test_echo_case_insensitive(self):
        res, close = handle_command(["eChO", "foo"])
        self.assertEqual(res, b"$3\r\nfoo\r\n")
        self.assertFalse(close)

    def test_echo_wrong_args(self):
        res, close = handle_command(["ECHO"])
        self.assertTrue(res.startswith(b"-ERR"))
        self.assertFalse(close)

    def test_quit(self):
        res, close = handle_command(["QUIT"])
        self.assertEqual(res, b"+OK\r\n")
        self.assertTrue(close)

    def test_quit_case_insensitive(self):
        res, close = handle_command(["qUiT"])
        self.assertEqual(res, b"+OK\r\n")
        self.assertTrue(close)

    def test_unknown_command(self):
        res, close = handle_command(["FOOBAR"])
        self.assertTrue(res.startswith(b"-ERR unknown command"))
        self.assertFalse(close)

    def test_empty_command(self):
        res, close = handle_command([])
        self.assertEqual(res, b"")
        self.assertFalse(close)


class TestServerIntegration(unittest.TestCase):
    """Integration tests for TCP socket handling and command processing."""

    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.new_event_loop()
        cls.thread = threading.Thread(target=cls.loop.run_forever, daemon=True)
        cls.thread.start()

        async def start_test_server():
            return await asyncio.start_server(handle_client, "127.0.0.1", 0)

        future = asyncio.run_coroutine_threadsafe(start_test_server(), cls.loop)
        cls.server = future.result()
        cls.port = cls.server.sockets[0].getsockname()[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.close()
        future = asyncio.run_coroutine_threadsafe(cls.server.wait_closed(), cls.loop)
        future.result()
        cls.loop.call_soon_threadsafe(cls.loop.stop)
        cls.thread.join()

    def _send_recv(self, data: bytes) -> bytes:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect(("127.0.0.1", self.port))
        try:
            sock.sendall(data)
            response = sock.recv(1024)
            return response
        finally:
            sock.close()

    def test_integration_ping(self):
        res = self._send_recv(b"*1\r\n$4\r\nPING\r\n")
        self.assertEqual(res, b"+PONG\r\n")

    def test_integration_ping_inline(self):
        res = self._send_recv(b"PING\r\n")
        self.assertEqual(res, b"+PONG\r\n")

    def test_integration_echo(self):
        res = self._send_recv(b"*2\r\n$4\r\nECHO\r\n$11\r\nhello world\r\n")
        self.assertEqual(res, b"$11\r\nhello world\r\n")

    def test_integration_quit(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect(("127.0.0.1", self.port))
        sock.sendall(b"*1\r\n$4\r\nQUIT\r\n")
        res = sock.recv(1024)
        self.assertEqual(res, b"+OK\r\n")
        res_after = sock.recv(1024)
        self.assertEqual(res_after, b"")
        sock.close()

    def test_integration_unknown_cmd(self):
        res = self._send_recv(b"*1\r\n$7\r\nUNKNOWN\r\n")
        self.assertTrue(res.startswith(b"-ERR"))

    def test_integration_multiple_commands_single_connection(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect(("127.0.0.1", self.port))

        sock.sendall(b"PING\r\n")
        res1 = sock.recv(1024)
        self.assertEqual(res1, b"+PONG\r\n")

        sock.sendall(b"*2\r\n$4\r\nECHO\r\n$4\r\ntest\r\n")
        res2 = sock.recv(1024)
        self.assertEqual(res2, b"$4\r\ntest\r\n")

        sock.close()


if __name__ == "__main__":
    unittest.main()
