import fnmatch

RESPValue = str | bytes | int | float | list["RESPValue"] | None


def encode_simple_string(val: str) -> bytes:
    return f"+{val}\r\n".encode("utf-8")


def encode_error(err_type: str, message: str) -> bytes:
    return f"-{err_type} {message}\r\n".encode("utf-8")


def encode_integer(val: int) -> bytes:
    return f":{val}\r\n".encode("utf-8")


def encode_bulk_string(val: bytes | str | None) -> bytes:
    if val is None:
        return b"$-1\r\n"
    if isinstance(val, str):
        b_val = val.encode("utf-8")
    else:
        b_val = val
    return f"${len(b_val)}\r\n".encode("utf-8") + b_val + b"\r\n"


def encode_array(arr: list[bytes] | list[str] | None) -> bytes:
    if arr is None:
        return b"*-1\r\n"
    res = [f"*{len(arr)}\r\n".encode("utf-8")]
    for item in arr:
        res.append(encode_bulk_string(item))
    return b"".join(res)


class RESPDecoder:
    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> None:
        self._buffer.extend(data)

    def decode_multi(self) -> list[list[bytes]]:
        cmds: list[list[bytes]] = []
        while True:
            saved = bytearray(self._buffer)
            cmd = self._decode_one()
            if cmd is None:
                self._buffer = saved
                break
            cmds.append(cmd)
        return cmds

    def _decode_one(self) -> list[bytes] | None:
        if not self._buffer:
            return None
        if self._buffer.startswith(b"*"):
            return self._decode_resp_array()
        else:
            return self._decode_inline()

    def _decode_inline(self) -> list[bytes] | None:
        idx = self._buffer.find(b"\r\n")
        if idx == -1:
            return None
        line = bytes(self._buffer[:idx])
        del self._buffer[: idx + 2]
        parts = line.split()
        return [p for p in parts]

    def _decode_resp_array(self) -> list[bytes] | None:
        idx = self._buffer.find(b"\r\n")
        if idx == -1:
            return None
        try:
            count = int(self._buffer[1:idx])
        except ValueError:
            del self._buffer[: idx + 2]
            return None
        del self._buffer[: idx + 2]
        if count < 0:
            return []
        args: list[bytes] = []
        for _ in range(count):
            arg = self._decode_bulk_string()
            if arg is None:
                return None
            args.append(arg)
        return args

    def _decode_bulk_string(self) -> bytes | None:
        if not self._buffer:
            return None
        if not self._buffer.startswith(b"$"):
            return None
        idx = self._buffer.find(b"\r\n")
        if idx == -1:
            return None
        try:
            length = int(self._buffer[1:idx])
        except ValueError:
            return None
        if length < 0:
            del self._buffer[: idx + 2]
            return b""
        start = idx + 2
        end = start + length
        if len(self._buffer) < end + 2:
            return None
        data = bytes(self._buffer[start:end])
        del self._buffer[: end + 2]
        return data


def glob_match(pattern: str, string: str) -> bool:
    return fnmatch.fnmatch(string, pattern)
