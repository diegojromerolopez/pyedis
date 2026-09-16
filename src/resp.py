from __future__ import annotations

from collections.abc import Iterable


def simple(value: str) -> bytes:
    return f"+{value}\r\n".encode()


def error(value: str) -> bytes:
    return f"-{value}\r\n".encode()


def integer(value: int) -> bytes:
    return f":{value}\r\n".encode()


def bulk(value: bytes | str | None) -> bytes:
    if value is None:
        return b"$-1\r\n"
    data = value.encode() if isinstance(value, str) else value
    return b"$" + str(len(data)).encode() + b"\r\n" + data + b"\r\n"


def array(values: Iterable[bytes | str | None]) -> bytes:
    encoded = b"".join(bulk(value) for value in values)
    values_list = list(values)
    encoded = b"".join(bulk(value) for value in values_list)
    return b"*" + str(len(values_list)).encode() + b"\r\n" + encoded


class Decoder:
    def __init__(self) -> None:
        self.buffer = bytearray()

    def feed(self, data: bytes) -> list[list[bytes]]:
        self.buffer.extend(data)
        result: list[list[bytes]] = []
        while True:
            parsed = self._one()
            if parsed is None:
                return result
            result.append(parsed)

    def _line(self, start: int) -> tuple[bytes, int] | None:
        end = self.buffer.find(b"\r\n", start)
        if end < 0:
            return None
        return bytes(self.buffer[start:end]), end + 2

    def _one(self) -> list[bytes] | None:
        if not self.buffer:
            return None
        if self.buffer[0] != ord("*"):
            line = self._line(0)
            if line is None:
                return None
            raw, end = line
            del self.buffer[:end]
            return raw.split()
        line = self._line(1)
        if line is None:
            return None
        try:
            count = int(line[0])
        except ValueError:
            del self.buffer[:line[1]]
            return []
        pos = line[1]
        values: list[bytes] = []
        for _ in range(count):
            if pos >= len(self.buffer) or self.buffer[pos:pos + 1] != b"$":
                return None
            header = self._line(pos + 1)
            if header is None:
                return None
            try:
                size = int(header[0])
            except ValueError:
                return None
            pos = header[1]
            if size < 0:
                values.append(b"")
                continue
            if len(self.buffer) < pos + size + 2:
                return None
            if self.buffer[pos + size:pos + size + 2] != b"\r\n":
                return None
            values.append(bytes(self.buffer[pos:pos + size]))
            pos += size + 2
        del self.buffer[:pos]
        return values
