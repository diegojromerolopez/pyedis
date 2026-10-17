"""PFADD domain operation."""

from .hll_codec import REGISTERS, add, decode, encode


def pfadd(store: object, key: str, values: list[bytes]) -> int:
    registers = bytearray(REGISTERS)
    existing = getattr(store, "_strings")[key] if getattr(store, "exists")(key) else None
    if existing is not None:
        registers = decode(existing.encode("latin1"))
    changed = any(add(registers, value) for value in values)
    getattr(store, "_strings")[key] = encode(registers).decode("latin1")
    return int(changed)
