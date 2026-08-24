from typing import Any, List, Optional, Tuple, Union


class SimpleString:
    def __init__(self, value: str) -> None:
        self.value = value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, SimpleString):
            return self.value == other.value
        return False

    def __repr__(self) -> str:
        return f"SimpleString({self.value!r})"


class Error:
    def __init__(self, message: str) -> None:
        self.message = message

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Error):
            return self.message == other.message
        return False

    def __repr__(self) -> str:
        return f"Error({self.message!r})"


class RESPError(Exception):
    """Raised when RESP protocol parsing encounters malformed data."""

    pass


class RESPIncompleteError(Exception):
    """Raised when the buffer does not contain enough data to complete parsing."""

    pass


# Encoders
def encode_simple_string(val: str) -> bytes:
    return f"+{val}\r\n".encode("utf-8")


def encode_error(val: str) -> bytes:
    return f"-{val}\r\n".encode("utf-8")


def encode_integer(val: int) -> bytes:
    return f":{val}\r\n".encode("ascii")


def encode_bulk_string(val: Optional[Union[str, bytes]]) -> bytes:
    if val is None:
        return b"$-1\r\n"
    if isinstance(val, str):
        b_val = val.encode("utf-8")
    else:
        b_val = val
    return f"${len(b_val)}\r\n".encode("ascii") + b_val + b"\r\n"


def encode_array(val: Optional[List[Any]]) -> bytes:
    if val is None:
        return b"*-1\r\n"
    out = f"*{len(val)}\r\n".encode("ascii")
    for item in val:
        out += encode_resp(item)
    return out


def encode_resp(val: Any) -> bytes:
    if isinstance(val, SimpleString):
        return encode_simple_string(val.value)
    elif isinstance(val, Error):
        return encode_error(val.message)
    elif isinstance(val, int):
        return encode_integer(val)
    elif isinstance(val, (str, bytes)):
        return encode_bulk_string(val)
    elif isinstance(val, list):
        return encode_array(val)
    elif val is None:
        return encode_bulk_string(None)
    else:
        raise TypeError(f"Cannot encode type {type(val)} to RESP")


# Decoders
def _find_crlf(data: bytes, start: int = 0) -> int:
    idx = data.find(b"\r\n", start)
    if idx == -1:
        raise RESPIncompleteError("Incomplete line, CRLF missing")
    return idx


def decode_resp(data: bytes) -> Tuple[Any, int]:
    """Parse a single RESP data structure from bytes.

    Returns:
        Tuple of (parsed_value, bytes_consumed).

    Raises:
        RESPIncompleteError: If more bytes are needed.
        RESPError: If data is malformed.
    """
    if not data:
        raise RESPIncompleteError("Empty buffer")

    prefix = data[0:1]

    if prefix == b"+":
        # Simple String
        crlf = _find_crlf(data, 1)
        val_bytes = data[1:crlf]
        try:
            val_str = val_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise RESPError(f"Invalid UTF-8 in simple string: {e}") from e
        return SimpleString(val_str), crlf + 2

    elif prefix == b"-":
        # Error
        crlf = _find_crlf(data, 1)
        msg_bytes = data[1:crlf]
        try:
            msg_str = msg_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise RESPError(f"Invalid UTF-8 in error message: {e}") from e
        return Error(msg_str), crlf + 2

    elif prefix == b":":
        # Integer
        crlf = _find_crlf(data, 1)
        num_bytes = data[1:crlf]
        try:
            num = int(num_bytes.decode("ascii"))
        except ValueError as e:
            raise RESPError(f"Invalid integer string: {num_bytes!r}") from e
        return num, crlf + 2

    elif prefix == b"$":
        # Bulk String
        crlf = _find_crlf(data, 1)
        len_str = data[1:crlf].decode("ascii", errors="replace")
        try:
            length = int(len_str)
        except ValueError as e:
            raise RESPError(f"Invalid bulk string length: {len_str!r}") from e

        if length == -1:
            return None, crlf + 2
        if length < -1:
            raise RESPError(f"Negative bulk string length: {length}")

        start_content = crlf + 2
        end_content = start_content + length
        if len(data) < end_content + 2:
            raise RESPIncompleteError("Incomplete bulk string payload")

        if data[end_content : end_content + 2] != b"\r\n":
            raise RESPError("Bulk string does not terminate with CRLF")

        return data[start_content:end_content], end_content + 2

    elif prefix == b"*":
        # Array
        crlf = _find_crlf(data, 1)
        count_str = data[1:crlf].decode("ascii", errors="replace")
        try:
            count = int(count_str)
        except ValueError as e:
            raise RESPError(f"Invalid array count: {count_str!r}") from e

        if count == -1:
            return None, crlf + 2
        if count < -1:
            raise RESPError(f"Negative array count: {count}")

        elements: List[Any] = []
        cursor = crlf + 2
        for _ in range(count):
            if cursor >= len(data):
                raise RESPIncompleteError("Incomplete array elements")
            elem, read_bytes = decode_resp(data[cursor:])
            elements.append(elem)
            cursor += read_bytes

        return elements, cursor

    else:
        raise RESPError(f"Unknown RESP prefix byte: {prefix!r}")


def parse_command(buffer: bytes) -> Tuple[Optional[List[bytes]], bytes]:
    """Parses a command (array of bulk strings or bytes) from the buffer.

    Returns:
        (list_of_args, remaining_buffer) if a complete command was parsed,
        (None, buffer) if incomplete.
    """
    if not buffer:
        return None, buffer

    # Inline command support e.g. PING\r\n
    if not buffer.startswith(b"*"):
        idx = buffer.find(b"\r\n")
        if idx == -1:
            return None, buffer
        line = buffer[:idx]
        remaining = buffer[idx + 2 :]
        parts = [p for p in line.split(b" ") if p]
        if not parts:
            return None, remaining
        return parts, remaining

    try:
        val, read_bytes = decode_resp(buffer)
    except RESPIncompleteError:
        return None, buffer

    if val is None:
        return [], buffer[read_bytes:]

    if not isinstance(val, list):
        raise RESPError("Command input must be an array")

    cmd_args: List[bytes] = []
    for item in val:
        if isinstance(item, bytes):
            cmd_args.append(item)
        elif isinstance(item, str):
            cmd_args.append(item.encode("utf-8"))
        elif isinstance(item, SimpleString):
            cmd_args.append(item.value.encode("utf-8"))
        else:
            raise RESPError(f"Invalid element type in command array: {type(item)}")

    return cmd_args, buffer[read_bytes:]
