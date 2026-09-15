"""RESP2 encoding and stream decoding."""
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
            except Incomplete:
                break
            except ProtocolError:
                raise
            result.append(value)
            self.buffer = self.buffer[used:]
        return result

    def finish(self) -> None:
        if self.buffer:
            raise ProtocolError("protocol error")

    def _parse(self, data: bytes) -> tuple[object, int]:
        if not data:
            raise Incomplete
        kind = data[:1]
        end = data.find(b"\r\n")
        if kind in b"+-:" and end >= 0:
            text = data[1:end]
            if kind == b":":
                try:
                    return int(text), end + 2
                except ValueError as exc:
                    raise ProtocolError("protocol error") from exc
            return text, end + 2
        if kind == b"$":
            if end < 0:
                raise Incomplete
            try:
                length = int(data[1:end])
            except ValueError as exc:
                raise ProtocolError("protocol error") from exc
            if length < -1:
                raise ProtocolError("protocol error")
            pos = end + 2
            if length == -1:
                return None, pos
            if len(data) < pos + length + 2:
                raise Incomplete
            if data[pos + length:pos + length + 2] != b"\r\n":
                raise ProtocolError("protocol error")
            return data[pos:pos + length], pos + length + 2
        if kind == b"*":
            if end < 0:
                raise Incomplete
            try:
                count = int(data[1:end])
            except ValueError as exc:
                raise ProtocolError("protocol error") from exc
            if count < -1:
                raise ProtocolError("protocol error")
            pos = end + 2
            if count == -1:
                return None, pos
            values: list[object] = []
            for _ in range(count):
                value, used = self._parse(data[pos:])
                values.append(value)
                pos += used
            return values, pos
        if kind not in b"+-:$*":
            line_end = data.find(b"\r\n")
            if line_end < 0:
                raise Incomplete
            parts = data[:line_end].split()
            if not parts:
                raise ProtocolError("protocol error")
            return parts, line_end + 2
        raise Incomplete


class Incomplete(Exception):
    """Input needs more bytes."""


def encode(value: object) -> bytes:
    if value is None:
        return b"$-1\r\n"
    if isinstance(value, int):
        return f":{value}\r\n".encode()
    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
        return b"$" + str(len(raw)).encode() + b"\r\n" + raw + b"\r\n"
    if isinstance(value, str):
        raw = value.encode()
        return b"$" + str(len(raw)).encode() + b"\r\n" + raw + b"\r\n"
    if isinstance(value, list):
        return b"*" + str(len(value)).encode() + b"\r\n" + b"".join(encode(item) for item in value)
    raise TypeError(f"unsupported RESP value: {type(value)}")


def simple(text: str) -> bytes:
    return b"+" + text.encode() + b"\r\n"


def error(text: str) -> bytes:
    return b"-" + text.encode() + b"\r\n"
