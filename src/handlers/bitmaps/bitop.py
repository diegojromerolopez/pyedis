"""Redis BITOP operations on binary-safe string values."""


def _value(store: object, key: str) -> bytes:
    if not getattr(store, "exists")(key):
        return b""
    return getattr(store, "_strings")[key].encode("latin1")


def bitop(store: object, operation: str, destination: str, keys: list[str]) -> int:
    """Apply AND, OR, XOR, or NOT and return the resulting byte length."""
    op = operation.upper()
    if op == "NOT":
        if len(keys) != 1:
            raise ValueError("BITOP NOT must be called with a single source key")
        source = _value(store, keys[0])
        result = bytes((~byte) & 255 for byte in source)
    else:
        if op not in {"AND", "OR", "XOR"} or not keys:
            raise ValueError("invalid BITOP operation")
        values = [_value(store, key) for key in keys]
        width = max((len(value) for value in values), default=0)
        result = bytearray(width)
        for index in range(width):
            operands = [value[index] if index < len(value) else 0 for value in values]
            if op == "AND":
                result[index] = operands[0]
                for operand in operands[1:]:
                    result[index] &= operand
            elif op == "OR":
                result[index] = 0
                for operand in operands:
                    result[index] |= operand
            else:
                result[index] = 0
                for operand in operands:
                    result[index] ^= operand
        result = bytes(result)
    getattr(store, "_strings")[destination] = result.decode("latin1")
    getattr(store, "_expires").pop(destination, None)
    return len(result)
