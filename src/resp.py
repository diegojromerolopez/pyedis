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
        b = data.encode("utf-8")
    else:
        b = data
    return f"${len(b)}\r\n".encode("utf-8") + b + b"\r\n"

def encode_array(items: list[Any] | None) -> bytes:
    if items is None:
        return b"*-1\r\n"
    res = [f"*{len(items)}\r\n".encode("utf-8")]
    for item in items:
        res.append(encode_resp(item))
    return b"".join(res)

def encode_resp(value: Any) -> bytes:
    if value is None:
        return encode_bulk_string(None)
    if isinstance(value, bool):
        return encode_integer(1 if value else 0)
    if isinstance(value, int):
        return encode_integer(value)
    if isinstance(value, (bytes, str)):
        return encode_bulk_string(value)
    if isinstance(value, list):
        return encode_array(value)
    if isinstance(value, Exception):
        return encode_error(str(value))
    return encode_simple_string(str(value))

def decode_resp_stream(buffer: bytearray) -> tuple[list[list[bytes]], bytearray]:
    commands: list[list[bytes]] = []
    idx = 0
    buf_len = len(buffer)

    while idx < buf_len:
        if buffer[idx] == ord("*"):
            # Multi-bulk array
            crlf = buffer.find(b"\r\n", idx)
            if crlf == -1:
                break
            try:
                num_elements = int(buffer[idx + 1 : crlf])
            except ValueError:
                break
            if num_elements < 0:
                idx = crlf + 2
                continue
            
            cur = crlf + 2
            parsed_args: list[bytes] = []
            valid = True
            for _ in range(num_elements):
                if cur >= buf_len or buffer[cur] != ord("$"):
                    valid = False
                    break
                elem_crlf = buffer.find(b"\r\n", cur)
                if elem_crlf == -1:
                    valid = False
                    break
                try:
                    arg_len = int(buffer[cur + 1 : elem_crlf])
                except ValueError:
                    valid = False
                    break
                cur = elem_crlf + 2
                if cur + arg_len + 2 > buf_len:
                    valid = False
                    break
                arg_data = bytes(buffer[cur : cur + arg_len])
                parsed_args.append(arg_data)
                cur += arg_len + 2
            
            if not valid:
                break
            commands.append(parsed_args)
            idx = cur
        else:
            # Inline command
            crlf = buffer.find(b"\r\n", idx)
            if crlf == -1:
                break
            line = buffer[idx:crlf].decode("utf-8", errors="replace").strip()
            if line:
                parts = [p.encode("utf-8") for p in line.split()]
                commands.append(parts)
            idx = crlf + 2

    return commands, buffer[idx:]
