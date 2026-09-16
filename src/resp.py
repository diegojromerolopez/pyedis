"""RESP2 encoding and streaming decoding."""
from __future__ import annotations

from dataclasses import dataclass, field


def simple(value: str) -> bytes:
    return b"+" + value.encode() + b"\r\n"


def error(value: str) -> bytes:
    return b"-" + value.encode() + b"\r\n"


def integer(value: int) -> bytes:
    return f":{value}\r\n".encode()


def bulk(value: bytes | str | None) -> bytes:
    if value is None:
        return b"$-1\r\n"
    data = value if isinstance(value, bytes) else value.encode()
    return f"${len(data)}\r\n".encode() + data + b"\r\n"


def array(values: list[bytes | str | None]) -> bytes:
    return f"*{len(values)}\r\n".encode() + b"".join(bulk(v) for v in values)


@dataclass
class Decoder:
    buffer: bytearray = field(default_factory=bytearray)

    def feed(self, data: bytes) -> list[list[bytes]]:
        self.buffer.extend(data)
        result: list[list[bytes]] = []
        while self.buffer:
            command = self._frame()
            if command is None:
                break
            result.append(command)
        return result

    def _line(self, start: int) -> tuple[bytes, int] | None:
        end = self.buffer.find(b"\r\n", start)
        if end < 0:
            return None
        return bytes(self.buffer[start:end]), end + 2

    def _frame(self) -> list[bytes] | None:
        if self.buffer[0] != ord("*"):
            line = self._line(0)
            if line is None:
                return None
            raw, end = line
            del self.buffer[:end]
            return raw.split()
        header = self._line(1)
        if header is None:
            return None
        try:
            count = int(header[0])
        except ValueError:
            del self.buffer[:header[1]]
            return []
        pos = header[1]
        values: list[bytes] = []
        for _ in range(count):
            if pos >= len(self.buffer) or self.buffer[pos] != ord("$"):
                return None
            length_line = self._line(pos + 1)
            if length_line is None:
                return None
            try:
                length = int(length_line[0])
            except ValueError:
                return None
            pos = length_line[1]
            if length < 0:
                values.append(b"")
                continue
            if len(self.buffer) < pos + length + 2:
                return None
            if self.buffer[pos + length:pos + length + 2] != b"\r\n":
                return None
            values.append(bytes(self.buffer[pos:pos + length]))
            pos += length + 2
        del self.buffer[:pos]
        return values
