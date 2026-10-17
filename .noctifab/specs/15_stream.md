### 6.13 Stream Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `XADD` | `XADD key [NOMKSTREAM] [MAXLEN\|MINID [=\|~] th [LIMIT c]] *\|id field val [field val ...]` | `$<len>\r\n<entry_id_string>\r\n` (or `$-1\r\n`) | ID less than top ID errors | `XADD mystream * sensor 1 temp 22.5` &rarr; `$15\r\n1724623200000-0\r\n` |
| `XREAD` | `XREAD [COUNT count] [BLOCK ms] STREAMS key [key ...] id [id ...]` | `*<streams_array>\r\n` (or `*-1\r\n` on block timeout) | Syntax/arity errors | `XREAD COUNT 1 STREAMS mystream 0-0` &rarr; `*1\r\n*2\r\n$8\r\nmystream\r\n*1...` |
| `XRANGE` | `XRANGE key start end [COUNT count]`<br>Returns stream entries within ID range. | `*<entries_array>\r\n` | Syntax/arity errors | `XRANGE mystream - + COUNT 10` &rarr; `*1\r\n*2\r\n$15\r\n1724623200000-0...` |
| `XREVRANGE` | `XREVRANGE key end start [COUNT count]`<br>Returns entries reverse ordered by ID. | `*<entries_array>\r\n` | Syntax/arity errors | `XREVRANGE mystream + - COUNT 1` &rarr; `*1\r\n*2\r\n$15\r\n1724623200000-0...` |
| `XLEN` | `XLEN key`<br>Returns number of entries in stream. | `:<count>\r\n` (0 if missing) | `!=1` arg errors | `XLEN mystream` &rarr; `:1\r\n` |
| `XTRIM` | `XTRIM key MAXLEN\|MINID [=\|~] threshold [LIMIT count]`<br>Trims stream entries. | `:<count_of_entries_deleted>\r\n` | Syntax/arity errors | `XTRIM mystream MAXLEN 1000` &rarr; `:0\r\n` |
| `XDEL` | `XDEL key id [id ...]`<br>Removes specified entries from stream by ID. | `:<count_of_entries_deleted>\r\n` | `<2` args errors | `XDEL mystream 1724623200000-0` &rarr; `:1\r\n` |
| `XINFO` | `XINFO STREAM\|GROUPS\|CONSUMERS [args]`<br>Returns stream and group inspection data. | `*<info_array>\r\n` | Stream not found errors | `XINFO STREAM mystream` &rarr; `*14\r\n$6\r\nlength\r\n:1...` |
| `XGROUP` | `XGROUP CREATE\|CREATECONSUMER\|DELCONSUMER\|DESTROY\|SETID [args]` | `+OK\r\n` or `:<deleted_count>\r\n` | Subcommand errors | `XGROUP CREATE mystream mygrp $ MKSTREAM` &rarr; `+OK\r\n` |
| `XREADGROUP` | `XREADGROUP GROUP group consumer [COUNT c] [BLOCK ms] [NOACK] STREAMS k ... id ...` | `*<streams_array>\r\n` | Group not found / syntax errors | `XREADGROUP GROUP mygrp c1 COUNT 1 STREAMS mystream >` &rarr; `*1...` |
| `XACK` | `XACK key group id [id ...]`<br>Acknowledges stream messages for consumer group. | `:<count_acknowledged>\r\n` | `<3` args errors | `XACK mystream mygrp 1724623200000-0` &rarr; `:1\r\n` |
| `XCLAIM` | `XCLAIM key group consumer min-idle-time id [id ...] [IDLE ms] [TIME ms] [RETRYCOUNT c]` | `*<claimed_entries>\r\n` | Syntax/arity errors | `XCLAIM mystream mygrp c2 3600000 1724623200000-0` &rarr; `*1...` |
| `XAUTOCLAIM` | `XAUTOCLAIM key group consumer min-idle-time start [COUNT count] [JUSTID]` | `*3\r\n$<len>\r\n<next_start>\r\n*<entries>\r\n*<deleted>\r\n` | Syntax/arity errors | `XAUTOCLAIM mystream mygrp c2 3600000 0-0 COUNT 1` &rarr; `*3...` |
| `XPENDING` | `XPENDING key group [[IDLE min-idle-time] start end count [consumer]]` | Summary array `*4...` or detailed entry list | Group not found errors | `XPENDING mystream mygrp` &rarr; `*4\r\n:0\r\n$-1\r\n$-1\r\n*0\r\n` |
