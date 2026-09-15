"""RESP2 encoding and streaming decoding."""
from __future__ import annotations

from dataclasses import dataclass


class ProtocolError(Exception):
    """Raised for malformed RESP input."""


@dataclass
class Decoder:
    buffer: bytes = b""

    def feed(self, data: bytes) -> list[object]:
        self.buffer += data
        result: list[object] = []
        while self.buffer:
            try:
                value, used = self._parse(self.buffer)
            except EOFError:
                break
            result.append(value)
            self.buffer = self.buffer[used:]
        return result

    def finish(self) -> None:
        if self.buffer:
            raise ProtocolError("incomplete request")

    def _parse(self, data: bytes) -> tuple[object, int]:
        if not data:
            raise EOFError
        marker = data[:1]
        end = data.find(b"\r\n")
        if end < 0:
            raise EOFError
        if marker == b"+":
            return data[1:end].decode("utf-8", "replace"), end + 2
        if marker == b"-":
            return RespError(data[1:end].decode("utf-8", "replace")), end + 2
        if marker == b":":
            try:
                return int(data[1:end]), end + 2
            except ValueError as exc:
                raise ProtocolError("integer") from exc
        if marker == b"$":
            try:
                length = int(data[1:end])
            except ValueError as exc:
                raise ProtocolError("bulk length") from exc
            if length == -1:
                return None, end + 2
            if length < -1:
                raise ProtocolError("bulk length")
            start = end + 2
            stop = start + length
            if len(data) < stop + 2:
                raise EOFError
            if data[stop:stop + 2] != b"\r\n":
                raise ProtocolError("bulk terminator")
            return data[start:stop], stop + 2
        if marker == b"*":
            try:
                count = int(data[1:end])
            except ValueError as exc:
                raise ProtocolError("array length") from exc
            if count == -1:
                return None, end + 2
            if count < -1:
                raise ProtocolError("array length")
            pos = end + 2
            values: list[object] = []
            for _ in range(count):
                value, used = self._parse(data[pos:])
                values.append(value)
                pos += used
            return values, pos
        raise ProtocolError("frame")


@dataclass(frozen=True)
class RespError:
    message: str


def encode(value: object) -> bytes:
    if isinstance(value, RespError):
        return b"-" + value.message.encode() + b"\r\n"
    if value is None:
        return b"$-1\r\n"
    if isinstance(value, bool):
        return b":" + (b"1" if value else b"0") + b"\r\n"
    if isinstance(value, int):
        return f":{value}\r\n".encode()
    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
        return b"$" + str(len(raw)).encode() + b"\r\n" + raw + b"\r\n"
    if isinstance(value, str):
        raw = value.encode()
        return b"+" + raw + b"\r\n"
    if isinstance(value, (list, tuple)):
        return b"*" + str(len(value)).encode() + b"\r\n" + b"".join(encode(item) for item in value)
    raise TypeError(f"unsupported RESP value: {type(value)!r}")


def inline(data: bytes) -> list[bytes] | None:
    if not data.endswith(b"\r\n"):
        return None
    return data[:-2].split()
