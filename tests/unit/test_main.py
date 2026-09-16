import asyncio
import unittest

from src.server import Store, encode_bulk, encode_simple, execute, parse_request


class RespAndCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = Store()

    def test_parse_and_ping(self) -> None:
        request = b"*1\r\n$4\r\nping\r\n"
        parts, remainder = parse_request(request)
        self.assertEqual(parts, [b"ping"])
        self.assertEqual(remainder, b"")
        response, close = execute(parts, self.store, 0)
        self.assertEqual(response, encode_simple(b"PONG"))
        self.assertFalse(close)

    def test_set_get_and_missing_key(self) -> None:
        execute([b"SET", b"name", b"pyedis"], self.store, 0)
        response, _ = execute([b"GET", b"name"], self.store, 0)
        self.assertEqual(response, encode_bulk(b"pyedis"))
        response, _ = execute([b"GET", b"missing"], self.store, 0)
        self.assertEqual(response, b"$-1\r\n")

    def test_failed_commands_return_resp_errors(self) -> None:
        response, close = execute([b"ECHO"], self.store, 0)
        self.assertTrue(response.startswith(b"-ERR "))
        self.assertFalse(close)
        response, _ = execute([b"NOPE"], self.store, 0)
        self.assertEqual(response, b"-ERR unknown command 'NOPE'\r\n")

    def test_mutating_commands(self) -> None:
        response, _ = execute([b"INCR", b"counter"], self.store, 0)
        self.assertEqual(response, b":1\r\n")
        response, _ = execute([b"DECR", b"counter"], self.store, 0)
        self.assertEqual(response, b":0\r\n")
        response, _ = execute([b"DEL", b"counter"], self.store, 0)
        self.assertEqual(response, b":1\r\n")
        response, _ = execute([b"EXISTS", b"counter"], self.store, 0)
        self.assertEqual(response, b":0\r\n")

    def test_quit_requests_connection_close(self) -> None:
        response, close = execute([b"QUIT"], self.store, 0)
        self.assertEqual(response, b"+OK\r\n")
        self.assertTrue(close)


class EntrypointTests(unittest.TestCase):
    def test_run_server_can_be_cancelled_without_persistence(self) -> None:
        async def scenario() -> None:
            from src.server import run_server

            task = asyncio.create_task(run_server("127.0.0.1", 0, "unused"))
            await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
