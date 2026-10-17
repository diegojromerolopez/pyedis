### 6.1 String Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `APPEND` | `APPEND key value`<br>Appends value to key string. Creates key if missing. | `:<new_string_length>\r\n` | `<2` args: `-ERR wrong number of arguments...`<br>Wrong Type: `-WRONGTYPE ...` | `APPEND msg " world"` &rarr; `:11\r\n` |
| `DECR` | `DECR key`<br>Decrements integer value of key by 1. | `:<new_int_value>\r\n` | Non-integer: `-ERR value is not an integer or out of range\r\n` | `DECR counter` &rarr; `:4\r\n` |
| `DECRBY` | `DECRBY key decrement`<br>Decrements key integer value by decrement amount. | `:<new_int_value>\r\n` | Non-integer: `-ERR value is not an integer or out of range\r\n` | `DECRBY counter 5` &rarr; `:-1\r\n` |
| `GET` | `GET key`<br>Returns string value of key. | `$<len>\r\n<val>\r\n`<br>`$-1\r\n` (if missing/expired) | Wrong Type: `-WRONGTYPE Operation against a key holding the wrong kind of value\r\n` | `GET user:1` &rarr; `$5\r\nAlice\r\n` |
| `GETDEL` | `GETDEL key`<br>Gets string value and atomically deletes the key. | `$<len>\r\n<val>\r\n`<br>`$-1\r\n` (if missing/expired) | Wrong Type: `-WRONGTYPE ...` | `GETDEL token` &rarr; `$4\r\nsecret\r\n` |
| `GETEX` | `GETEX key [EX s\|PX ms\|EXAT ts\|PXAT ms-ts\|PERSIST]`<br>Gets value and updates/clears TTL. | `$<len>\r\n<val>\r\n`<br>`$-1\r\n` (if missing/expired) | Syntax/Range errors | `GETEX session EX 300` &rarr; `$8\r\nactive_1\r\n` |
| `GETRANGE` | `GETRANGE key start end`<br>Returns substring from start to end (supports negative offsets). | `$<len>\r\n<substring>\r\n` | `!=3` args: `-ERR wrong number of arguments...` | `GETRANGE msg 0 4` &rarr; `$5\r\nHello\r\n` |
| `GETSET` | `GETSET key value`<br>Atomically sets string value and returns old value. | `$<len>\r\n<old_val>\r\n`<br>`$-1\r\n` (if missing) | `!=2` args: `-ERR wrong number of arguments...` | `GETSET count "10"` &rarr; `$1\r\n5\r\n` |
| `INCR` | `INCR key`<br>Increments key integer value by 1 (initializes to "0" if missing). | `:<new_int_value>\r\n` | Non-integer: `-ERR value is not an integer or out of range\r\n` | `INCR hits` &rarr; `:1\r\n` |
| `INCRBY` | `INCRBY key increment`<br>Increments key integer value by given integer increment. | `:<new_int_value>\r\n` | Non-integer: `-ERR value is not an integer or out of range\r\n` | `INCRBY score 10` &rarr; `:15\r\n` |
| `INCRBYFLOAT` | `INCRBYFLOAT key increment`<br>Increments key float value by given float increment. | `$<len>\r\n<new_float_str>\r\n` | Non-float: `-ERR value is not a valid float\r\n` | `INCRBYFLOAT temp 2.5` &rarr; `$4\r\n22.5\r\n` |
| `LCS` | `LCS key1 key2 [LEN] [IDX] [MINMATCHLEN len] [WITHMATCHLEN]`<br>Computes Longest Common Subsequence between two strings. | String: `$<len>\r\n<seq>\r\n`<br>LEN: `:<len>\r\n`<br>IDX: `*<matches>` | Key missing or wrong type errors | `LCS key1 key2` &rarr; `$4\r\nabcd\r\n`<br>`LCS key1 key2 LEN` &rarr; `:4\r\n` |
| `MGET` | `MGET key [key ...]`<br>Returns values of all specified keys in order. | `*<count>\r\n$<len>\r\n<v1>\r\n...` (with `$-1\r\n` for missing) | `<1` arg: `-ERR wrong number of arguments...` | `MGET k1 k2` &rarr; `*2\r\n$1\r\na\r\n$-1\r\n` |
| `MSET` | `MSET key value [key value ...]`<br>Sets multiple key-value pairs atomically. | `+OK\r\n` | Odd arguments: `-ERR wrong number of arguments...` | `MSET a "1" b "2"` &rarr; `+OK\r\n` |
| `MSETNX` | `MSETNX key value [key value ...]`<br>Sets multiple pairs only if NONE of the keys exist. | `:1\r\n` (all set)<br>`:0\r\n` (none set) | Odd arguments: `-ERR wrong number of arguments...` | `MSETNX a "1" c "3"` &rarr; `:0\r\n` |
| `PSETEX` | `PSETEX key milliseconds value`<br>Sets value with millisecond TTL. | `+OK\r\n` | Invalid TTL: `-ERR value is not an integer or out of range\r\n` | `PSETEX k 500 "val"` &rarr; `+OK\r\n` |
| `SET` | `SET key value [EX s\|PX ms\|EXAT ts\|PXAT ms-ts\|KEEPTTL] [NX\|XX] [GET]`<br>Sets string with options. | `+OK\r\n` (or old val if `GET`)<br>`$-1\r\n` (if condition failed) | `<2` args or both `NX` & `XX`: `-ERR syntax error\r\n` | `SET k v EX 60 NX` &rarr; `+OK\r\n` |
| `SETEX` | `SETEX key seconds value`<br>Sets value with second TTL. | `+OK\r\n` | Invalid TTL: `-ERR value is not an integer or out of range\r\n` | `SETEX k 10 "val"` &rarr; `+OK\r\n` |
| `SETNX` | `SETNX key value`<br>Sets value only if key does not exist. | `:1\r\n` (set)<br>`:0\r\n` (not set) | `!=2` args: `-ERR wrong number of arguments...` | `SETNX lock "held"` &rarr; `:1\r\n` |
| `SETRANGE` | `SETRANGE key offset value`<br>Overwrites part of string starting at offset. | `:<length_after_modification>\r\n` | `!=3` args: `-ERR wrong number of arguments...` | `SETRANGE k 6 "Redis"` &rarr; `:11\r\n` |
| `STRLEN` | `STRLEN key`<br>Returns length of string value. | `:<len>\r\n` (0 if missing) | `!=1` arg: `-ERR wrong number of arguments...` | `STRLEN k` &rarr; `:5\r\n` |
| `SUBSTR` | `SUBSTR key start end`<br>Alias for `GETRANGE`. | `$<len>\r\n<substring>\r\n` | `!=3` args: `-ERR wrong number of arguments...` | `SUBSTR k 0 2` &rarr; `$3\r\nHel\r\n` |
