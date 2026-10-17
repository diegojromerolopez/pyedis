"""RESP wire-protocol encoders and a streaming command decoder."""

from typing import Any


def encode_simple_string(value: str) -> bytes:
    return f"+{value}\r\n".encode("utf-8")


def encode_error(msg: str, err_type: str = "ERR") -> bytes:
    return f"-{err_type} {msg}\r\n".encode("utf-8")


def encode_integer(value: int) -> bytes:
    return f":{value}\r\n".encode("ascii")


def encode_bulk_string(data: bytes | str | None) -> bytes:
    if data is None:
        return b"$-1\r\n"
    payload = data.encode("utf-8") if isinstance(data, str) else data
    return f"${len(payload)}\r\n".encode("ascii") + payload + b"\r\n"


def encode_array(items: list[Any] | None) -> bytes:
    if items is None:
        return b"*-1\r\n"
    return f"*{len(items)}\r\n".encode("ascii") + b"".join(encode_resp(item) for item in items)


def encode_resp(value: Any) -> bytes:
    if value is None:
        return encode_bulk_string(None)
    if isinstance(value, bool):
        return encode_integer(int(value))
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


def _line_end(buffer: bytearray, start: int) -> int | None:
    position = buffer.find(b"\r\n", start)
    return position if position >= 0 else None


def _parse_command(buffer: bytearray, start: int) -> tuple[list[bytes], int] | None:
    """Parse one array-of-bulk-strings command, or return None if incomplete."""
    end = _line_end(buffer, start)
    if end is None:
        return None
    try:
        count = int(buffer[start + 1 : end])
    except ValueError:
        return ([], end + 2)
    if count < 0:
        return ([], end + 2)

    cursor = end + 2
    command: list[bytes] = []
    for _ in range(count):
        if cursor >= len(buffer):
            return None
        if buffer[cursor : cursor + 1] != b"$":
            return ([], cursor)
        header_end = _line_end(buffer, cursor)
        if header_end is None:
            return None
        try:
            size = int(buffer[cursor + 1 : header_end])
        except ValueError:
            return ([], header_end + 2)
        if size < 0:
            command.append(b"")
            cursor = header_end + 2
            continue
        payload_start = header_end + 2
        payload_end = payload_start + size
        if payload_end + 2 > len(buffer):
            return None
        if buffer[payload_end : payload_end + 2] != b"\r\n":
            return ([], payload_end + 2)
        command.append(bytes(buffer[payload_start:payload_end]))
        cursor = payload_end + 2
    return command, cursor


def decode_resp_stream(buffer: bytearray) -> tuple[list[list[bytes]], bytearray]:
    """Decode complete commands, retaining any incomplete trailing bytes."""
    commands: list[list[bytes]] = []
    cursor = 0
    while cursor < len(buffer):
        if buffer[cursor : cursor + 1] == b"*":
            parsed = _parse_command(buffer, cursor)
            if parsed is None:
                break
            command, next_cursor = parsed
            if command or next_cursor > cursor:
                if command:
                    commands.append(command)
                cursor = next_cursor
                continue
            break

        end = _line_end(buffer, cursor)
        if end is None:
            break
        line = bytes(buffer[cursor:end]).strip()
        cursor = end + 2
        if line:
            commands.append(line.split())

    return commands, bytearray(buffer[cursor:])
