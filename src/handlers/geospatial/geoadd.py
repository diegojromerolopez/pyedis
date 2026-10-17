"""GEOADD command parsing and application."""

from dataclasses import dataclass

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
    nx = xx = ch = False
    data: list[str] = []
    for argument in args[1:]:
        option = argument.upper()
        if option in {"NX", "XX", "CH"}:
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
        else:
            data.append(argument)

    if nx and xx or len(data) < 3 or len(data) % 3:
        if nx and xx:
            return GeoAddResult(encode_error("syntax error"), False)
        return GeoAddResult(encode_error("wrong number of arguments for 'geoadd' command"), False)

    additions: list[tuple[float, str]] = []
    for index in range(0, len(data), 3):
        try:
            longitude = float(data[index])
            latitude = float(data[index + 1])
        except ValueError:
            return GeoAddResult(encode_error("not a valid float"), False)
        if not validate_coordinates(longitude, latitude):
            return GeoAddResult(encode_error("invalid longitude,latitude pair"), False)
        additions.append((float(encode(longitude, latitude)), data[index + 2]))

    existing_before = set(store._zsets.get(key, {}))
    added = changed = 0
    try:
        for score, member in additions:
            was_added, was_changed = store.geoadd(key, score, member, nx=nx, xx=xx)
            # A member first encountered in this command contributes to the
            # GEOADD count even if a later duplicate updates its score.
            if was_added or (member not in existing_before and was_changed):
                added += 1
            changed += int(was_changed)
    except ValueError as error:
        return GeoAddResult(encode_error(str(error)), False)
    return GeoAddResult(encode_integer(changed if ch else added), changed > 0)


def geoadd(store: Store, args: list[str]) -> bytes:
    return execute_geoadd(store, args).reply
