"""Handlers for commands that manage client connection state."""

from dataclasses import dataclass

from src.resp import (
    encode_array,
    encode_bulk_string,
    encode_error,
    encode_integer,
    encode_simple_string,
)


@dataclass
class ConnectionState:
    """State belonging to one logical client connection."""

    name: str | None = None
    database: int = 0
    protocol: int = 2


def execute_client(state: ConnectionState, args: list[str]) -> bytes:
    """Execute the supported CLIENT subcommands."""
    if not args:
        return encode_error("syntax error")
    subcommand = args[0].upper()
    if subcommand == "SETNAME":
        if len(args) != 2 or not args[1]:
            return encode_error("wrong number of arguments for 'client|setname' command")
        state.name = args[1]
        return encode_simple_string("OK")
    if subcommand == "GETNAME":
        if len(args) != 1:
            return encode_error("syntax error")
        return encode_bulk_string(state.name)
    if subcommand == "ID":
        if len(args) != 1:
            return encode_error("syntax error")
        return encode_integer(1)
    return encode_error("syntax error")


def execute_hello(state: ConnectionState, args: list[str]) -> bytes:
    """Negotiate RESP2/RESP3 and return the standard HELLO map as an array."""
    if len(args) > 1:
        return encode_error("syntax error")
    if args:
        try:
            protocol = int(args[0])
        except ValueError:
            return encode_error("NOPROTO unsupported protocol version")
        if protocol not in (2, 3):
            return encode_error("NOPROTO unsupported protocol version")
        state.protocol = protocol
    return encode_array(
        [
            "server",
            "pyedis",
            "version",
            "1.0.0",
            "proto",
            state.protocol,
            "id",
            1,
            "mode",
            "standalone",
            "role",
            "master",
            "modules",
            [],
        ]
    )


def execute_select(state: ConnectionState, args: list[str]) -> bytes:
    """Select one of the sixteen logical databases."""
    if len(args) != 1:
        return encode_error("wrong number of arguments for 'select' command")
    try:
        database = int(args[0])
    except ValueError:
        return encode_error("invalid DB index")
    if database < 0 or database > 15:
        return encode_error("invalid DB index")
    state.database = database
    return encode_simple_string("OK")


def execute_info(args: list[str]) -> bytes:
    """Return a compact INFO response suitable for client negotiation."""
    if any(not section for section in args):
        return encode_error("syntax error")
    return encode_bulk_string(
        "# Server\r\npyedis_version:1.0.0\r\nredis_version:7.0.0\r\nuptime_in_seconds:0\r\n"
    )
