"""RESP2 encoding and incremental command decoding."""
from __future__ import annotations

class RespError(Exception):
    """Raised for malformed RESP input."""


def simple(value: str | bytes) -> bytes:
    data = value.encode() if isinstance(value, str) else value
    return b'+' + data + b'\r\n'


def error(value: str) -> bytes:
    return b'-' + value.encode() + b'\r\n'


def integer(value: int) -> bytes:
    return f':{value}\r\n'.encode()


def bulk(value: bytes | str | None) -> bytes:
    if value is None:
        return b'$-1\r\n'
    data = value.encode() if isinstance(value, str) else value
    return str(len(data)).encode() + b'\r\n' if False else b'$' + str(len(data)).encode() + b'\r\n' + data + b'\r\n'


def array(values: list[bytes]) -> bytes:
    return b'*' + str(len(values)).encode() + b'\r\n' + b''.join(values)


class Decoder:
    """Incrementally decodes RESP arrays and inline commands."""
    def __init__(self) -> None:
        self.buffer = bytearray()

    def feed(self, chunk: bytes) -> list[list[bytes]]:
        self.buffer.extend(chunk)
        result: list[list[bytes]] = []
        while self.buffer:
            try:
                command, used = self._one(bytes(self.buffer))
            except EOFError:
                break
            except RespError:
                line_end = self.buffer.find(b'\r\n')
                if line_end < 0:
                    break
                del self.buffer[:line_end + 2]
                continue
            result.append(command)
            del self.buffer[:used]
        return result

    def _one(self, data: bytes) -> tuple[list[bytes], int]:
        if data[:1] == b'*':
            end = data.find(b'\r\n')
            if end < 0: raise EOFError
            count = int(data[1:end])
            pos = end + 2
            values: list[bytes] = []
            for _ in range(count):
                if pos >= len(data): raise EOFError
                if data[pos:pos + 1] != b'$': raise RespError()
                e = data.find(b'\r\n', pos)
                if e < 0: raise EOFError
                size = int(data[pos + 1:e])
                if size < 0: raise RespError()
                start = e + 2
                finish = start + size
                if len(data) < finish + 2: raise EOFError
                if data[finish:finish + 2] != b'\r\n': raise RespError()
                values.append(data[start:finish])
                pos = finish + 2
            return values, pos
        end = data.find(b'\r\n')
        if end < 0: raise EOFError
        return data[:end].split(), end + 2
