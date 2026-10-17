"""RESP wire protocol encoder and streaming decoder."""

from typing import Any


def encode_simple_string(s: str) -> bytes:
    return f"+{s}\r\n".encode("utf-8")


def encode_error(msg: str, err_type: str = "ERR") -> bytes:
    return f"-{err_type} {msg}\r\n".encode("utf-8")


def encode_integer(n: int) -> bytes:
    return f":{n}\r\n".encode("utf-8")


def encode_bulk_string(data: bytes | str | None) -> bytes:
    if data is None:
        return b"$-1\r\n"
    if isinstance(data, str):
        b_data = data.encode("utf-8")
    else:
        b_data = data
    return f"${len(b_data)}\r\n".encode("utf-8") + b_data + b"\r\n"


def encode_array(items: list[Any] | None) -> bytes:
    if items is None:
        return b"*-1\r\n"
    res = f"*{len(items)}\r\n".encode("utf-8")
    for item in items:
        res += encode_resp(item)
    return res


def encode_resp(value: Any) -> bytes:
    if value is None:
        return encode_bulk_string(None)
    if isinstance(value, bool):
        return encode_integer(1 if value else 0)
    if isinstance(value, int):
        return encode_integer(value)
    if isinstance(value, float):
        return encode_bulk_string(str(value))
    if isinstance(value, str):
        return encode_bulk_string(value)
    if isinstance(value, (bytes, bytearray)):
        return encode_bulk_string(bytes(value))
    if isinstance(value, list):
        return encode_array(value)
    return encode_error("unsupported payload type")


def decode_resp_stream(buffer: bytearray) -> tuple[list[list[bytes]], bytearray]:
    commands: list[list[bytes]] = []
    idx = 0
    buf_len = len(buffer)

    while idx < buf_len:
        if buffer[idx : idx + 1] == b"*":
            line_end = buffer.find(b"\r\n", idx)
            if line_end == -1:
                break
            try:
                num_elements = int(buffer[idx + 1 : line_end])
            except ValueError:
                idx = line_end + 2
                continue
            curr = line_end + 2
            cmd: list[bytes] = []
            parsed_ok = True
            for _ in range(num_elements):
                if curr >= buf_len or buffer[curr : curr + 1] != b"$":
                    parsed_ok = False
                    break
                elem_line_end = buffer.find(b"\r\n", curr)
                if elem_line_end == -1:
                    parsed_ok = False
                    break
                try:
                    elem_len = int(buffer[curr + 1 : elem_line_end])
                except ValueError:
                    parsed_ok = False
                    break
                elem_start = elem_line_end + 2
                elem_end = elem_start + elem_len
                if elem_end + 2 > buf_len or buffer[elem_end : elem_end + 2] != b"\r\n":
                    parsed_ok = False
                    break
                cmd.append(bytes(buffer[elem_start:elem_end]))
                curr = elem_end + 2
            if not parsed_ok:
                break
            commands.append(cmd)
            idx = curr
        else:
            line_end = buffer.find(b"\r\n", idx)
            if line_end == -1:
                break
            line = bytes(buffer[idx:line_end]).strip()
            idx = line_end + 2
            if line:
                parts = line.split()
                commands.append(parts)

    return commands, buffer[idx:]
