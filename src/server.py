"""Asyncio RESP2 server implementation."""

from __future__ import annotations

import asyncio
import signal
from dataclasses import dataclass, field


@dataclass
class Store:
    """In-memory key/value state used by the server."""

    values: dict[bytes, bytes] = field(default_factory=dict)
    expirations: dict[bytes, float] = field(default_factory=dict)

    def _expired(self, key: bytes, now: float) -> bool:
        expires = self.expirations.get(key)
        if expires is not None and expires <= now:
            self.values.pop(key, None)
            self.expirations.pop(key, None)
            return True
        return False

    def get(self, key: bytes, now: float) -> bytes | None:
        if self._expired(key, now):
            return None
        return self.values.get(key)

    def set(self, key: bytes, value: bytes) -> None:
        self.values[key] = value
        self.expirations.pop(key, None)

    def delete(self, keys: list[bytes], now: float) -> int:
        return sum(
            self.get(key, now) is not None and self.values.pop(key, None) is not None
            for key in keys
        )


class RespError(Exception):
    """A malformed RESP request."""


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
    return (
        b"*"
        + str(len(values)).encode()
        + b"\r\n"
        + b"".join(encode_bulk(value) for value in values)
    )


def parse_request(data: bytes) -> tuple[list[bytes], bytes]:
    if not data.startswith(b"*"):
        raise RespError("expected array")
    line_end = data.find(b"\r\n")
    if line_end < 0:
        raise RespError("invalid request")
    try:
        count = int(data[1:line_end])
    except ValueError as exc:
        raise RespError("invalid array length") from exc
    if count < 0:
        raise RespError("invalid array length")
    position = line_end + 2
    parts: list[bytes] = []
    for _ in range(count):
        if position >= len(data) or data[position : position + 1] != b"$":
            raise RespError("expected bulk string")
        end = data.find(b"\r\n", position)
        if end < 0:
            raise RespError("invalid bulk string")
        try:
            length = int(data[position + 1 : end])
        except ValueError as exc:
            raise RespError("invalid bulk length") from exc
        if length < 0:
            raise RespError("null bulk string")
        start = end + 2
        finish = start + length
        if finish + 2 > len(data) or data[finish : finish + 2] != b"\r\n":
            raise RespError("incomplete bulk string")
        parts.append(data[start:finish])
        position = finish + 2
    return parts, data[position:]


def execute(parts: list[bytes], store: Store, now: float) -> tuple[bytes, bool]:
    if not parts:
        return encode_error("empty command"), False
    command = parts[0].upper()
    args = parts[1:]
    if command == b"PING":
        if len(args) > 1:
            return encode_error("wrong number of arguments for 'ping' command"), False
        return (encode_bulk(args[0]) if args else encode_simple(b"PONG")), False
    if command == b"ECHO":
        if len(args) != 1:
            return encode_error("wrong number of arguments for 'echo' command"), False
        return encode_bulk(args[0]), False
    if command == b"QUIT":
        return encode_simple(b"OK"), True
    if command == b"SET":
        if len(args) != 2:
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
        return encode_integer(
            sum(store.get(key, now) is not None for key in args)
        ), False
    if command in (b"INCR", b"DECR"):
        if len(args) != 1:
            name = command.decode().lower()
            return encode_error(
                f"wrong number of arguments for '{name}' command"
            ), False
        current = store.get(args[0], now)
        try:
            value = int(current or b"0") + (1 if command == b"INCR" else -1)
        except ValueError:
            return encode_error("value is not an integer or out of range"), False
        store.set(args[0], str(value).encode())
        return encode_integer(value), False
    if command == b"FLUSHALL":
        if args:
            return encode_error(
                "wrong number of arguments for 'flushall' command"
            ), False
        store.values.clear()
        store.expirations.clear()
        return encode_simple(b"OK"), False
    return encode_error("unknown command"), False


async def _read_request(reader: asyncio.StreamReader) -> list[bytes]:
    first = await reader.readline()
    if not first:
        raise asyncio.IncompleteReadError(partial=b"", expected=1)
    if first.startswith(b"*"):
        try:
            count = int(first[1:-2])
        except ValueError as exc:
            raise RespError("invalid array length") from exc
        if count < 0:
            raise RespError("invalid array length")
        request = first
        for _ in range(count):
            header = await reader.readline()
            if not header.startswith(b"$"):
                raise RespError("expected bulk string")
            try:
                length = int(header[1:-2])
            except ValueError as exc:
                raise RespError("invalid bulk length") from exc
            if length < 0:
                raise RespError("null bulk string")
            body = await reader.readexactly(length + 2)
            request += header + body
        parts, _ = parse_request(request)
        return parts
    if not first.endswith(b"\r\n"):
        raise RespError("invalid inline command")
    return first[:-2].split()


async def client_session(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, store: Store
) -> None:
    try:
        while True:
            try:
                parts = await _read_request(reader)
                response, close = execute(
                    parts, store, asyncio.get_running_loop().time()
                )
            except (RespError, ValueError, asyncio.IncompleteReadError):
                response, close = encode_error("protocol error"), False
                if isinstance(_, asyncio.IncompleteReadError):
                    break
            writer.write(response)
            await writer.drain()
            if close:
                break
    except (ConnectionError, asyncio.IncompleteReadError):
        return
    finally:
        writer.close()
        await writer.wait_closed()


async def run_server(
    host: str = "127.0.0.1", port: int = 6379, data_dir: str | None = None
) -> None:
    """Listen for clients until cancellation or SIGINT/SIGTERM."""
    del data_dir
    store = Store()
    server = await asyncio.start_server(
        lambda reader, writer: client_session(reader, writer, store), host, port
    )
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    for name in ("SIGINT", "SIGTERM"):
        try:
            loop.add_signal_handler(getattr(signal, name), stopped.set)
        except (NotImplementedError, RuntimeError):
            continue
    async with server:
        await stopped.wait()
