### 6.2 Bitmaps & Bitfield Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `SETBIT` | `SETBIT key offset value`<br>Sets or clears bit at offset (0 or 1). | `:0\r\n` or `:1\r\n` (original bit) | Offset out of range errors | `SETBIT bits 7 1` &rarr; `:0\r\n` |
| `GETBIT` | `GETBIT key offset`<br>Returns bit value at offset (0 or 1). | `:0\r\n` or `:1\r\n` | `!=2` args errors | `GETBIT bits 7` &rarr; `:1\r\n` |
| `BITCOUNT` | `BITCOUNT key [start end [BYTE\|BIT]]`<br>Counts set bits (population count) in string. | `:<count>\r\n` | Syntax/range errors | `BITCOUNT bits` &rarr; `:1\r\n` |
| `BITPOS` | `BITPOS key bit [start [end [BYTE\|BIT]]]`<br>Finds position of first bit set to 0 or 1. | `:<position>\r\n` (-1 if not found) | Syntax/range errors | `BITPOS bits 1` &rarr; `:7\r\n` |
| `BITOP` | `BITOP AND\|OR\|XOR\|NOT destkey srckey [srckey ...]`<br>Performs bitwise operations. | `:<dest_string_length>\r\n` | Syntax/arity errors | `BITOP AND dest k1 k2` &rarr; `:2\r\n` |
| `BITFIELD` | `BITFIELD key [GET type off] [SET type off val] [INCRBY type off inc] [OVERFLOW WRAP\|SAT\|FAIL]` | `*<results_array>\r\n` | Syntax/arity errors | `BITFIELD mykey GET u4 0` &rarr; `*1\r\n:5\r\n` |
