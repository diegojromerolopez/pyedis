from typing import Any


def encode_resp(data: Any) -> bytes:
    if data is None:
        return b"$-1\r\n"
    if isinstance(data, bool):
        return b"+OK\r\n" if data else b"$-1\r\n"
    if isinstance(data, int):
        return f":{data}\r\n".encode("utf-8")
    if isinstance(data, str):
        encoded = data.encode("utf-8")
        return f"${len(encoded)}\r\n".encode("utf-8") + encoded + b"\r\n"
    if isinstance(data, bytes):
        return f"${len(data)}\r\n".encode("utf-8") + data + b"\r\n"
    if isinstance(data, list):
        res = [f"*{len(data)}\r\n".encode("utf-8")]
        for item in data:
            res.append(encode_resp(item))
        return b"".join(res)
    if isinstance(data, Exception):
        return f"-ERR {str(data)}\r\n".encode("utf-8")
    return encode_resp(str(data))


def encode_error(msg: str) -> bytes:
    return f"-ERR {msg}\r\n".encode("utf-8")


def encode_simple_string(msg: str) -> bytes:
    return f"+{msg}\r\n".encode("utf-8")


class RESPParser:
    def __init__(self) -> None:
        self._buf = bytearray()

    def feed(self, data: bytes) -> None:
        self._buf.extend(data)

    def parse_one(self) -> list[bytes] | None:
        if not self._buf:
            return None
        if self._buf.startswith(b"*"):
            return self._parse_array()
        if b"\r\n" in self._buf:
            idx = self._buf.index(b"\r\n")
            line = bytes(self._buf[:idx])
            del self._buf[: idx + 2]
            return [part for part in line.split(b" ") if part]
        return None

    def _parse_array(self) -> list[bytes] | None:
        idx = self._buf.find(b"\r\n")
        if idx == -1:
            return None
        try:
            count = int(self._buf[1:idx])
        except ValueError:
            del self._buf[: idx + 2]
            return None

        if count == -1:
            del self._buf[: idx + 2]
            return []

        curr = idx + 2
        args: list[bytes] = []
        for _ in range(count):
            if curr >= len(self._buf):
                return None
            if self._buf[curr : curr + 1] != b"$":
                return None
            next_line = self._buf.find(b"\r\n", curr)
            if next_line == -1:
                return None
            try:
                arg_len = int(self._buf[curr + 1 : next_line])
            except ValueError:
                return None
            curr = next_line + 2
            if len(self._buf) < curr + arg_len + 2:
                return None
            args.append(bytes(self._buf[curr : curr + arg_len]))
            curr += arg_len + 2

        del self._buf[:curr]
        return args
