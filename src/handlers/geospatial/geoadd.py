"""GEOADD command parsing and application."""

from dataclasses import dataclass
import math

from src.handlers.geospatial.geohash_codec import encode, validate_coordinates
from src.resp import encode_error, encode_integer
from src.store import Store


@dataclass(frozen=True)
class GeoAddResult:
    reply: bytes
    changed: bool


def execute_geoadd(store: Store, args: list[str]) -> GeoAddResult:
    if len(args) < 4:
        return GeoAddResult(encode_error("wrong number of arguments for 'geoadd' command"), False)
    key = args[0]
    index = 1
    nx = xx = ch = False
    while index < len(args) and args[index].upper() in {"NX", "XX", "CH"}:
        option = args[index].upper()
        if option == "NX":
            if nx:
                return GeoAddResult(encode_error("syntax error"), False)
            nx = True
        elif option == "XX":
            if xx:
                return GeoAddResult(encode_error("syntax error"), False)
            xx = True
        else:
            if ch:
                return GeoAddResult(encode_error("syntax error"), False)
            ch = True
        index += 1
    if nx and xx or index >= len(args) or (len(args) - index) % 3:
        return GeoAddResult(encode_error("syntax error"), False)

    additions: list[tuple[float, str]] = []
    for index in range(index, len(args), 3):
        try:
            longitude = float(args[index])
            latitude = float(args[index + 1])
        except ValueError:
            return GeoAddResult(encode_error("not a valid float"), False)
        if not validate_coordinates(longitude, latitude):
            return GeoAddResult(encode_error("invalid longitude,latitude pair"), False)
        additions.append((float(encode(longitude, latitude)), args[index + 2]))

    added = changed = 0
    try:
        for score, member in additions:
            was_added, was_changed = store.geoadd(key, score, member, nx=nx, xx=xx)
            added += int(was_added)
            changed += int(was_changed)
    except ValueError as error:
        return GeoAddResult(encode_error(str(error)), False)
    return GeoAddResult(encode_integer(changed if ch else added), changed > 0)


def geoadd(store: Store, args: list[str]) -> bytes:
    return execute_geoadd(store, args).reply
