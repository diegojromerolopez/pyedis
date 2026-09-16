"""Asyncio TCP server and backwards-compatible command helpers."""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from dataclasses import dataclass, field

PING_RESP = b"+PONG\r\n"
RESP_PING = b"*1\r\n$4\r\nPING\r\n"


class ProtocolError(Exception):
    """Raised when a client sends an unsupported request."""


@dataclass
class Store:
    """Small synchronous store retained for command-level compatibility tests."""

    values: dict[bytes, bytes] = field(default_factory=dict)
    expirations: dict[bytes, float] = field(default_factory=dict)

    def _expired(self, key: bytes, now: float) -> bool:
        expiry = self.expirations.get(key)
        if expiry is not None and expiry <= now:
            self.values.pop(key, None)
            self.expirations.pop(key, None)
            return True
        return False

    def get(self, key: bytes, now: float) -> bytes | None:
        self._expired(key, now)
        return self.values.get(key)

    def set(self, key: bytes, value: bytes) -> None:
        self.values[key] = value
        self.expirations.pop(key, None)

    def delete(self, keys: list[bytes], now: float) -> int:
        count = 0
        for key in keys:
            self._expired(key, now)
            if key in self.values:
                del self.values[key]
                self.expirations.pop(key, None)
                count += 1
        return count


def encode_simple(value: bytes) -> bytes:
    return b"+" + value + b"\r\n"


def encode_error(message: str) -> bytes:
    return b"-ERR " + message.encode() + b"\r\n"


def encode_integer(value: int) -> bytes:
    return f":{value}\r\n".encode()


def encode_bulk(value: bytes | None) -> bytes:
    if value is None:
        return b"$-1\r\n"
    return b"$" + str(len(value)).encode() + b"\r\n" + value + b"\r\n"


def encode_array(values: list[bytes]) -> bytes:
    return b"*" + str(len(values)).encode() + b"\r\n" + b"".join(encode_bulk(value) for value in values)


def parse_request(data: bytes) -> tuple[list[bytes], bytes]:
    if not data.startswith(b"*"):
        raise ProtocolError("expected array")
    end = data.find(b"\r\n")
    if end < 0:
        raise ProtocolError("invalid array length")
    try:
        count = int(data[1:end])
    except ValueError as exc:
        raise ProtocolError("invalid array length") from exc
    if count < 0:
        raise ProtocolError("invalid array length")
    position = end + 2
    parts: list[bytes] = []
    for _ in range(count):
        if position >= len(data) or data[position : position + 1] != b"$":
            raise ProtocolError("expected bulk string")
        line_end = data.find(b"\r\n", position)
        if line_end < 0:
            raise ProtocolError("invalid bulk string")
        try:
            length = int(data[position + 1 : line_end])
        except ValueError as exc:
            raise ProtocolError("invalid bulk length") from exc
        if length < 0:
            raise ProtocolError("null bulk string")
        start = line_end + 2
        finish = start + length
        if data[finish : finish + 2] != b"\r\n":
            raise ProtocolError("incomplete bulk string")
        parts.append(data[start:finish])
        position = finish + 2
    return parts, data[position:]


def execute(parts: list[bytes], store: Store, now: float) -> tuple[bytes, bool]:
    if not parts:
        return encode_error("empty command"), False
    command = parts[0].upper()
    args = parts[1:]
    name = command.decode(errors="replace").lower()
    if command == b"PING":
        if len(args) > 1:
            return encode_error("wrong number of arguments for 'ping' command"), False
        return (encode_bulk(args[0]) if args else encode_simple(b"PONG")), False
    if command == b"ECHO":
        if len(args) != 1:
            return encode_error("wrong number of arguments for 'echo' command"), False
        return encode_bulk(args[0]), False
    if command == b"QUIT":
        if args:
            return encode_error("wrong number of arguments for 'quit' command"), False
        return encode_simple(b"OK"), True
    if command == b"SET":
        if len(args) < 2:
            return encode_error("wrong number of arguments for 'set' command"), False
        store.set(args[0], args[1])
        return encode_simple(b"OK"), False
    if command == b"GET":
        if len(args) != 1:
            return encode_error("wrong number of arguments for 'get' command"), False
        return encode_bulk(store.get(args[0], now)), False
    if command == b"DEL":
        if not args:
            return encode_error("wrong number of arguments for 'del' command"), False
        return encode_integer(store.delete(args, now)), False
    if command == b"EXISTS":
        if not args:
            return encode_error("wrong number of arguments for 'exists' command"), False
        return encode_integer(sum(store.get(key, now) is not None for key in args)), False
    if command in (b"INCR", b"DECR"):
        if len(args) != 1:
            return encode_error(f"wrong number of arguments for '{name}' command"), False
        current = store.get(args[0], now) or b"0"
        try:
            value = int(current) + (1 if command == b"INCR" else -1)
        except ValueError:
            return encode_error("value is not an integer or out of range"), False
        store.set(args[0], str(value).encode())
        return encode_integer(value), False
    if command == b"FLUSHALL":
        if args:
            return encode_error("wrong number of arguments for 'flushall' command"), False
        store.values.clear()
        store.expirations.clear()
        return encode_simple(b"OK"), False
    return encode_error(f"unknown command '{parts[0].decode(errors='replace')}'"), False


async def client_session(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Serve supported PING requests until EOF or a protocol error."""
    try:
        while True:
            first = await reader.readline()
            if not first:
                break
            if first == b"PING\r\n" or first.upper() == b"PING\r\n":
                request = first
            elif first == b"*1\r\n":
                header = await reader.readline()
                if header != b"$4\r\n":
                    raise ProtocolError("expected PING")
                body = await reader.readexactly(6)
                if body.upper() != b"PING\r\n":
                    raise ProtocolError("expected PING")
                request = first + header + body
            else:
                raise ProtocolError("expected PING")
            if request == RESP_PING or request.upper() in (b"PING\r\n", RESP_PING):
                writer.write(PING_RESP)
                await writer.drain()
    except (ProtocolError, asyncio.IncompleteReadError, ConnectionError):
        pass
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except ConnectionError:
            pass


class Server:
    """Controllable asyncio server suitable for in-process tests."""

    def __init__(self, host: str = "127.0.0.1", port: int = 6379) -> None:
        self.host = host
        self.port = port
        self._server: asyncio.AbstractServer | None = None

    @property
    def address(self) -> tuple[str, int]:
        if self._server is None or not self._server.sockets:
            raise RuntimeError("server is not started")
        host, port = self._server.sockets[0].getsockname()[:2]
        return str(host), int(port)

    async def start(self) -> tuple[str, int]:
        if self._server is None:
            self._server = await asyncio.start_server(client_session, self.host, self.port)
            self.host, self.port = self.address
        return self.address

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def serve_forever(self) -> None:
        if self._server is None:
            await self.start()
        assert self._server is not None
        await self._server.serve_forever()


async def run_server(host: str = "127.0.0.1", port: int | None = None, data_dir: str | None = None) -> None:
    del data_dir
    try:
        selected_port = int(os.getenv("PORT", "6379")) if port is None else port
    except ValueError as exc:
        print(f"pyedis: invalid port: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    server = Server(host, selected_port)
    try:
        await server.start()
    except OSError as exc:
        print(f"pyedis: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signal_name in ("SIGINT", "SIGTERM"):
        try:
            loop.add_signal_handler(getattr(signal, signal_name), stopped.set)
        except (NotImplementedError, RuntimeError):
            continue
    try:
        await stopped.wait()
    finally:
        await server.stop()
