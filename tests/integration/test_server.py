from __future__ import annotations

import os
import select
import signal
import socket
import subprocess
import sys
import time
import unittest


class ServerIntegrationTests(unittest.TestCase):
    def test_ping(self) -> None:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]

        environment = os.environ.copy()
        environment["PORT"] = str(port)
        process = subprocess.Popen(
            [sys.executable, "-m", "src.main"],
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        connection: socket.socket | None = None
        deadline = time.monotonic() + 10
        try:
            while time.monotonic() < deadline:
                candidate = socket.socket()
                candidate.settimeout(0.1)
                try:
                    candidate.connect(("127.0.0.1", port))
                    connection = candidate
                    break
                except OSError:
                    candidate.close()
                if process.poll() is not None:
                    self.fail("server exited before becoming ready")
                select.select([], [], [], 0.02)
            self.assertIsNotNone(connection, "server did not become ready")
            assert connection is not None
            connection.sendall(b"PING\r\n")
            self.assertEqual(connection.recv(64), b"+PONG\r\n")
        finally:
            if connection is not None:
                connection.close()
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            self.assertEqual(process.returncode, 0)


if __name__ == "__main__":
    unittest.main()
