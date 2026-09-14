from __future__ import annotations


class IncompleteFrame(Exception):
    """Raised internally when a frame needs more bytes."""


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


def _line(data: bytes, start: int) -> tuple[bytes, int]:
    end = data.find(b"\r\n", start)
    if end < 0:
        raise IncompleteFrame
    return data[start:end], end + 2


def _frame(data: bytes, pos: int) -> tuple[bytes, int]:
    if pos >= len(data):
        raise IncompleteFrame
    prefix = data[pos:pos + 1]
    line, cursor = _line(data, pos + 1)
    if prefix in (b"+", b"-", b":"):
        return line, cursor
    if prefix == b"$":
        try:
            size = int(line)
        except ValueError as exc:
            raise ValueError("invalid bulk length") from exc
        if size == -1:
            return b"", cursor
        end = cursor + size
        if len(data) < end + 2 or data[end:end + 2] != b"\r\n":
            raise IncompleteFrame
        return data[cursor:end], end + 2
    if prefix == b"*":
        count = int(line)
        if count < 0:
            return b"", cursor
        result: list[bytes] = []
        for _ in range(count):
            value, cursor = _frame(data, cursor)
            result.append(value)
        return b"\x00".join(result), cursor
    raise ValueError("invalid RESP prefix")


class Decoder:
    """Incremental RESP array and inline command decoder."""

    def __init__(self) -> None:
        self.buffer = bytearray()

    def feed(self, chunk: bytes) -> list[list[bytes]]:
        self.buffer.extend(chunk)
        commands: list[list[bytes]] = []
        while self.buffer:
            try:
                if self.buffer[:1] == b"*":
                    value, used = _frame(bytes(self.buffer), 0)
                    parts = value.split(b"\x00") if value else []
                else:
                    end = self.buffer.find(b"\r\n")
                    if end < 0:
                        raise IncompleteFrame
                    raw = bytes(self.buffer[:end])
                    used = end + 2
                    parts = raw.split()
                if not parts:
                    del self.buffer[:used]
                    continue
                commands.append(parts)
                del self.buffer[:used]
            except IncompleteFrame:
                break
        return commands
