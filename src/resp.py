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
    """Decode complete commands from *buffer*, retaining an incomplete tail.

    Redis clients commonly split one frame across several socket reads and may
    send several frames in one read.  The cursor only advances after a whole
    command has been validated, so an incomplete frame is returned unchanged.
    Inline commands are retained for compatibility with the original server.
    """
    commands: list[list[bytes]] = []
    idx = 0
    length = len(buffer)

    while idx < length:
        if buffer[idx : idx + 1] != b"*":
            line_end = buffer.find(b"\r\n", idx)
            if line_end < 0:
                break
            line = bytes(buffer[idx:line_end]).strip()
            idx = line_end + 2
            if line:
                commands.append(line.split())
            continue

        header_end = buffer.find(b"\r\n", idx)
        if header_end < 0:
            break
        try:
            element_count = int(buffer[idx + 1 : header_end])
        except ValueError:
            idx = header_end + 2
            continue
        if element_count < 0:
            idx = header_end + 2
            continue

        cursor = header_end + 2
        command: list[bytes] = []
        complete = True
        for _ in range(element_count):
            if cursor >= length or buffer[cursor : cursor + 1] != b"$":
                complete = False
                break
            element_header_end = buffer.find(b"\r\n", cursor)
            if element_header_end < 0:
                complete = False
                break
            try:
                element_length = int(buffer[cursor + 1 : element_header_end])
            except ValueError:
                complete = False
                break
            if element_length < 0:
                complete = False
                break
            element_start = element_header_end + 2
            element_end = element_start + element_length
            if element_end + 2 > length:
                complete = False
                break
            if buffer[element_end : element_end + 2] != b"\r\n":
                complete = False
                break
            command.append(bytes(buffer[element_start:element_end]))
            cursor = element_end + 2

        if not complete:
            break
        commands.append(command)
        idx = cursor

    # Consume parsed frames while retaining only the incomplete suffix.  Return
    # a fresh bytearray so callers can safely extend it on the next read.
    return commands, bytearray(buffer[idx:])
