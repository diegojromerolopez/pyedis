"""PFCOUNT domain operation."""

from .hll_codec import decode, estimate


def pfcount(store: object, keys: list[str]) -> int:
    if not keys:
        return 0
    merged = bytearray(16384)
    for key in keys:
        if getattr(store, "exists")(key):
            registers = decode(getattr(store, "_strings")[key].encode("latin1"))
            for index, value in enumerate(registers):
                if value > merged[index]:
                    merged[index] = value
    return estimate(merged)
