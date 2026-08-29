"""Command router for pyedis."""

from typing import List, Tuple
from src.resp import encode_simple_string, encode_bulk_string, encode_error


def handle_command(args: List[str]) -> Tuple[bytes, bool]:
    """
    Processes a parsed command argument list.
    Returns tuple of (response_bytes, should_close_connection).
    """
    if not args:
        return b"", False

    cmd = args[0].upper()

    if cmd == "PING":
        if len(args) == 1:
            return encode_simple_string("PONG"), False
        elif len(args) == 2:
            return encode_bulk_string(args[1]), False
        else:
            return encode_error("ERR wrong number of arguments for 'ping' command"), False

    elif cmd == "ECHO":
        if len(args) == 2:
            return encode_bulk_string(args[1]), False
        else:
            return encode_error("ERR wrong number of arguments for 'echo' command"), False

    elif cmd == "QUIT":
        return encode_simple_string("OK"), True

    else:
        return encode_error(f"ERR unknown command '{args[0]}'"), False
