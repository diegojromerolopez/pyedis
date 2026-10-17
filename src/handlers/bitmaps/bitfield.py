"""BITFIELD integer extraction and mutation operations."""


def _parse_type(type_name: str) -> tuple[bool, int]:
    if len(type_name) < 2 or type_name[0].lower() not in {"i", "u"}:
        raise ValueError("invalid BITFIELD type")
    try:
        width = int(type_name[1:])
    except ValueError as exc:
        raise ValueError("invalid BITFIELD type") from exc
    if not 1 <= width <= 64:
        raise ValueError("invalid BITFIELD type")
    return type_name[0].lower() == "i", width


def _offset(value: str) -> int:
    if value.startswith("#"):
        raise ValueError("scaled offsets are not supported")
    result = int(value)
    if result < 0:
        raise ValueError("offset must be non-negative")
    return result


def _read(data: bytearray, start: int, signed: bool, width: int) -> int:
    value = 0
    for bit in range(width):
        position = start + bit
        value = (value << 1) | (
            (data[position // 8] >> (7 - position % 8)) & 1 if position // 8 < len(data) else 0
        )
    if signed and value & (1 << (width - 1)):
        value -= 1 << width
    return value


def _write(data: bytearray, start: int, width: int, value: int) -> None:
    needed = (start + width + 7) // 8
    data.extend(b"\\x00" * (needed - len(data)))
    for bit in range(width):
        position = start + bit
        mask = 1 << (7 - position % 8)
        if value & (1 << (width - bit - 1)):
            data[position // 8] |= mask
        else:
            data[position // 8] &= ~mask


def bitfield(store: object, key: str, commands: list[str]) -> list[int | None]:
    """Execute BITFIELD subcommands and return one reply per GET/SET/INCRBY."""
    data = bytearray(
        getattr(store, "_strings")[key].encode("latin1") if getattr(store, "exists")(key) else b""
    )
    replies: list[int | None] = []
    overflow = "WRAP"
    index = 0
    while index < len(commands):
        command = commands[index].upper()
        if command == "OVERFLOW":
            if index + 1 >= len(commands) or commands[index + 1].upper() not in {
                "WRAP",
                "SAT",
                "FAIL",
            }:
                raise ValueError("invalid overflow mode")
            overflow = commands[index + 1].upper()
            index += 2
            continue
        if command not in {"GET", "SET", "INCRBY"}:
            raise ValueError("invalid BITFIELD subcommand")
        needed = 2 if command == "GET" else 3
        if index + needed >= len(commands):
            raise ValueError("wrong number of arguments")
        signed, width = _parse_type(commands[index + 1])
        start = _offset(commands[index + 2])
        old = _read(data, start, signed, width)
        if command == "GET":
            replies.append(old)
            index += 3
            continue
        amount = int(commands[index + 3])
        target = amount if command == "SET" else old + amount
        minimum = -(1 << (width - 1)) if signed else 0
        maximum = (1 << (width - 1)) - 1 if signed else (1 << width) - 1
        if target < minimum or target > maximum:
            if overflow == "FAIL":
                replies.append(None)
                index += 4
                continue
            if overflow == "SAT":
                target = min(maximum, max(minimum, target))
            else:
                target %= 1 << width
                if signed and target >= 1 << (width - 1):
                    target -= 1 << width
        encoded = target if target >= 0 else target + (1 << width)
        _write(data, start, width, encoded)
        replies.append(old)
        index += 4
    getattr(store, "_strings")[key] = bytes(data).decode("latin1")
    getattr(store, "_expires").pop(key, None)
    return replies
