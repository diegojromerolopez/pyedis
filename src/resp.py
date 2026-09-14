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
    raw = value if isinstance(value, bytes) else value.encode()
    return b"$" + str(len(raw)).encode() + b"\r\n" + raw + b"\r\n"


def array(values: list[bytes]) -> bytes:
    return b"*" + str(len(values)).encode() + b"\r\n" + b"".join(values)


@dataclass
class Decoder:
    buffer: bytearray = field(default_factory=bytearray)

    def feed(self, data: bytes) -> list[list[bytes]]:
        self.buffer.extend(data)
        result: list[list[bytes]] = []
        while self.buffer:
            if self.buffer[:1] == b"*":
                frame = self._array()
            else:
                frame = self._inline()
            if frame is None:
                break
            result.append(frame)
        return result

    def _line(self, start: int = 0) -> tuple[bytes, int] | None:
        end = self.buffer.find(b"\r\n", start)
        if end < 0:
            return None
        return bytes(self.buffer[start:end]), end + 2

    def _array(self) -> list[bytes] | None:
        header = self._line()
        if header is None:
            return None
        try:
            count = int(header[0][1:])
        except ValueError:
            del self.buffer[: header[1]]
            return []
        pos = header[1]
        values: list[bytes] = []
        for _ in range(count):
            if pos >= len(self.buffer) or self.buffer[pos : pos + 1] != b"$":
                return None
            line = self._line(pos)
            if line is None:
                return None
            try:
                size = int(line[0][1:])
            except ValueError:
                return None
            pos = line[1]
            if size < 0:
                values.append(b"")
                continue
            if len(self.buffer) < pos + size + 2:
                return None
            if self.buffer[pos + size : pos + size + 2] != b"\r\n":
                return None
            values.append(bytes(self.buffer[pos : pos + size]))
            pos += size + 2
        del self.buffer[:pos]
        return values

    def _inline(self) -> list[bytes] | None:
        line = self._line()
        if line is None:
            return None
        del self.buffer[: line[1]]
        return line[0].split()
