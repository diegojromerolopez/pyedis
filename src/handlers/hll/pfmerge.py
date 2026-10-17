"""PFMERGE domain operation."""

from .hll_codec import REGISTERS, decode, encode


def pfmerge(store: object, destination: str, sources: list[str]) -> None:
    merged = bytearray(REGISTERS)
    for key in sources:
        if getattr(store, "exists")(key):
            registers = decode(getattr(store, "_strings")[key].encode("latin1"))
            for index, value in enumerate(registers):
                if value > merged[index]:
                    merged[index] = value
    getattr(store, "_strings")[destination] = encode(merged).decode("latin1")
