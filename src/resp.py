'''RESP (REdis Serialization Protocol) parser and serializer.'''

from typing import Any, List, Optional, Union


def encode_simple_string(s: str) -> bytes:
    return f"+{s}\r\n".encode("utf-8")


def encode_error(msg: str) -> bytes:
    return f"-{msg}\r\n".encode("utf-8")


def encode_integer(n: int) -> bytes:
    return f":{n}\r\n".encode("utf-8")


def encode_bulk_string(s: Union[str, bytes, None]) -> bytes:
    if s is None:
        return b"$-1\r\n"
    if isinstance(s, str):
        data = s.encode("utf-8")
    else:
        data = s
    return f"${len(data)}\r\n".encode("utf-8") + data + b"\r\n"


def encode_array(arr: Optional[List[Any]]) -> bytes:
    if arr is None:
        return b"*-1\r\n"
    out = [f"*{len(arr)}\r\n".encode("utf-8")]
    for item in arr:
        if isinstance(item, (str, bytes)) or item is None:
            out.append(encode_bulk_string(item))
        elif isinstance(item, int):
            out.append(encode_integer(item))
        elif isinstance(item, list):
            out.append(encode_array(item))
        else:
            out.append(encode_bulk_string(str(item)))
    return b"".join(out)


async def parse_resp_command(reader) -> Optional[List[str]]:
    """
    Reads a single command from asyncio.StreamReader.
    Supports RESP arrays (*N) and inline space-delimited commands.
    Returns list of arguments as strings, or None on EOF.
    """
    line = await reader.readline()
    if not line:
        return None
    
    line_str = line.decode("utf-8", errors="replace").rstrip("\r\n")
    if not line_str:
        return []

    if line.startswith(b"*"):
        try:
            num_elements = int(line_str[1:])
        except ValueError:
            return None
        if num_elements < 0:
            return None
        
        args = []
        for _ in range(num_elements):
            arg_header = await reader.readline()
            if not arg_header:
                return None
            arg_header_str = arg_header.decode("utf-8", errors="replace").rstrip("\r\n")
            if not arg_header_str.startswith("$"):
                return None
            try:
                length = int(arg_header_str[1:])
            except ValueError:
                return None
            if length == -1:
                args.append("")
                continue
            data = await reader.readexactly(length + 2)
            args.append(data[:-2].decode("utf-8", errors="replace"))
        return args
    else:
        return line_str.split()
