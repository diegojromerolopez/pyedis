"""Dense HyperLogLog encoding and cardinality estimation."""

import hashlib
import math

REGISTERS = 16384
_MAGIC = b"HLL1"


def encode(registers: bytes | bytearray) -> bytes:
    if len(registers) != REGISTERS:
        raise ValueError("invalid HyperLogLog register count")
    if any(value > 63 for value in registers):
        raise ValueError("invalid HyperLogLog register value")
    return _MAGIC + bytes(registers)


def decode(payload: bytes) -> bytearray:
    if len(payload) != REGISTERS + len(_MAGIC) or not payload.startswith(_MAGIC):
        raise ValueError("invalid HyperLogLog payload")
    registers = bytearray(payload[len(_MAGIC) :])
    if any(value > 63 for value in registers):
        raise ValueError("invalid HyperLogLog register value")
    return registers


def add(registers: bytearray, value: bytes) -> bool:
    digest = hashlib.sha256(value).digest()
    number = int.from_bytes(digest[:8], "big")
    index = number >> 50
    remainder = number & ((1 << 50) - 1)
    if remainder == 0:
        rank = 51
    else:
        rank = 1 + (50 - remainder.bit_length())
    rank = min(rank, 63)
    if rank > registers[index]:
        registers[index] = rank
        return True
    return False


def estimate(registers: bytes | bytearray) -> int:
    if len(registers) != REGISTERS:
        raise ValueError("invalid HyperLogLog register count")
    alpha = 0.7213 / (1 + 1.079 / REGISTERS)
    total = sum(2.0**-value for value in registers)
    result = alpha * REGISTERS * REGISTERS / total
    zeros = registers.count(0)
    if result <= 2.5 * REGISTERS and zeros:
        result = REGISTERS * math.log(REGISTERS / zeros)
    return max(0, int(round(result)))
