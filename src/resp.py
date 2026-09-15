"""RESP2 encoding and incremental decoding."""
from __future__ import annotations

from dataclasses import dataclass

@dataclass
class Frame:
    value: bytes | list[Frame] | None
    kind: bytes

class ProtocolError(Exception):
    pass

class Decoder:
    def __init__(self) -> None:
        self.buffer = b''

    def feed(self, data: bytes) -> list[Frame]:
        self.buffer += data
        result: list[Frame] = []
        while self.buffer:
            try:
                frame, end = self._parse(0)
            except EOFError:
                break
            except (ValueError, IndexError) as exc:
                raise ProtocolError from exc
            result.append(frame)
            self.buffer = self.buffer[end:]
        return result

    def _parse(self, pos: int) -> tuple[Frame, int]:
        if pos >= len(self.buffer):
            raise EOFError
        prefix = self.buffer[pos:pos + 1]
        if prefix == b'*':
            line, pos = self._line(pos + 1)
            count = int(line)
            if count < 0:
                return Frame(None, b'*'), pos
            values: list[Frame] = []
            for _ in range(count):
                item, pos = self._parse(pos)
                values.append(item)
            return Frame(values, b'*'), pos
        if prefix == b'$':
            line, pos = self._line(pos + 1)
            size = int(line)
            if size < 0:
                return Frame(None, b'$'), pos
            end = pos + size
            if end + 2 > len(self.buffer):
                raise EOFError
            if self.buffer[end:end + 2] != b'\r\n':
                raise ValueError
            return Frame(self.buffer[pos:end], b'$'), end + 2
        if prefix in (b'+', b'-', b':'):
            line, end = self._line(pos + 1)
            return Frame(line, prefix), end
        end = self.buffer.find(b'\r\n', pos)
        if end < 0:
            raise EOFError
        return Frame(self.buffer[pos:end].split(), b'i'), end + 2

    def _line(self, pos: int) -> tuple[bytes, int]:
        end = self.buffer.find(b'\r\n', pos)
        if end < 0:
            raise EOFError
        return self.buffer[pos:end], end + 2

def encode(value: object) -> bytes:
    if value is None:
        return b'$-1\r\n'
    if isinstance(value, int):
        return f':{value}\r\n'.encode()
    if isinstance(value, bytes):
        return b'$' + str(len(value)).encode() + b'\r\n' + value + b'\r\n'
    if isinstance(value, str):
        return b'+' + value.encode() + b'\r\n'
    if isinstance(value, list):
        return b'*' + str(len(value)).encode() + b'\r\n' + b''.join(encode(x) for x in value)
    raise TypeError(value)
