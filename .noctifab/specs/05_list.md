### 6.3 List Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `LPUSH` | `LPUSH key element [element ...]`<br>Prepends elements to list head. | `:<len_after_push>\r\n` | Wrong Type: `-WRONGTYPE ...` | `LPUSH list a b` &rarr; `:2\r\n` |
| `RPUSH` | `RPUSH key element [element ...]`<br>Appends elements to list tail. | `:<len_after_push>\r\n` | Wrong Type: `-WRONGTYPE ...` | `RPUSH list c` &rarr; `:3\r\n` |
| `LPUSHX` | `LPUSHX key element [element ...]`<br>Prepends elements only if list exists. | `:<len_after_push>\r\n` (0 if missing) | `<2` args errors | `LPUSHX list z` &rarr; `:4\r\n` |
| `RPUSHX` | `RPUSHX key element [element ...]`<br>Appends elements only if list exists. | `:<len_after_push>\r\n` (0 if missing) | `<2` args errors | `RPUSHX missing x` &rarr; `:0\r\n` |
| `LPOP` | `LPOP key [count]`<br>Removes and returns first element(s) from list. | `$<len>\r\n<elem>\r\n` or `*<count>` (or `$-1\r\n`) | `<1` arg errors | `LPOP list` &rarr; `$1\r\nb\r\n` |
| `RPOP` | `RPOP key [count]`<br>Removes and returns last element(s) from list. | `$<len>\r\n<elem>\r\n` or `*<count>` (or `$-1\r\n`) | `<1` arg errors | `RPOP list` &rarr; `$1\r\nc\r\n` |
| `LRANGE` | `LRANGE key start stop`<br>Returns range of elements from list. | `*<count>\r\n$<len>\r\n<elem1>...` | `!=3` args errors | `LRANGE list 0 -1` &rarr; `*2\r\n$1\r\nb\r\n$1\r\na\r\n` |
| `LLEN` | `LLEN key`<br>Returns length of list. | `:<length>\r\n` (0 if missing) | `!=1` arg errors | `LLEN list` &rarr; `:2\r\n` |
| `LINDEX` | `LINDEX key index`<br>Returns element at index (zero-based). | `$<len>\r\n<elem>\r\n` or `$-1\r\n` | `!=2` args errors | `LINDEX list 0` &rarr; `$1\r\nb\r\n` |
| `LSET` | `LSET key index element`<br>Sets list element at index. | `+OK\r\n` | Index out of range errors | `LSET list 0 "new"` &rarr; `+OK\r\n` |
| `LINSERT` | `LINSERT key BEFORE\|AFTER pivot element`<br>Inserts element relative to pivot. | `:<new_len>\r\n` (-1 if no pivot) | Syntax/arity errors | `LINSERT list BEFORE a x` &rarr; `:3\r\n` |
| `LREM` | `LREM key count element`<br>Removes count occurrences of element. | `:<count_removed>\r\n` | `!=3` args errors | `LREM list 1 a` &rarr; `:1\r\n` |
| `LTRIM` | `LTRIM key start stop`<br>Trims list to specified range. | `+OK\r\n` | `!=3` args errors | `LTRIM list 0 1` &rarr; `+OK\r\n` |
| `LMOVE` | `LMOVE source destination LEFT\|RIGHT LEFT\|RIGHT`<br>Moves element between lists. | `$<len>\r\n<elem>\r\n` or `$-1\r\n` | Syntax/arity errors | `LMOVE src dst RIGHT LEFT` &rarr; `$1\r\nx\r\n` |
| `LPOS` | `LPOS key element [RANK rank] [COUNT num] [MAXLEN len]`<br>Returns matching index/indices. | `:<index>\r\n` or `*<indices>\r\n` or `$-1\r\n` | Syntax/arity errors | `LPOS list a` &rarr; `:0\r\n` |
| `RPOPLPUSH` | `RPOPLPUSH source destination`<br>Atomically moves last element to destination head. | `$<len>\r\n<elem>\r\n` or `$-1\r\n` | `!=2` args errors | `RPOPLPUSH q1 q2` &rarr; `$3\r\njob\r\n` |
| `BLPOP` | `BLPOP key [key ...] timeout`<br>Blocking pop from head of first non-empty list. | `*2\r\n$<len>\r\n<key>\r\n$<len>\r\n<val>\r\n` or `*-1\r\n` | `<2` args errors | `BLPOP q 1` &rarr; `*2\r\n$1\r\nq\r\n$1\r\na\r\n` |
| `BRPOP` | `BRPOP key [key ...] timeout`<br>Blocking pop from tail of first non-empty list. | `*2\r\n$<len>\r\n<key>\r\n$<len>\r\n<val>\r\n` or `*-1\r\n` | `<2` args errors | `BRPOP q 1` &rarr; `*2\r\n$1\r\nq\r\n$1\r\nb\r\n` |
| `BLMOVE` | `BLMOVE source destination LEFT\|RIGHT LEFT\|RIGHT timeout`<br>Blocking atomic move between lists. | `$<len>\r\n<elem>\r\n` or `$-1\r\n` | Syntax/arity errors | `BLMOVE s d RIGHT LEFT 2` &rarr; `$1\r\na\r\n` |
| `BRPOPLPUSH` | `BRPOPLPUSH source destination timeout`<br>Blocking atomic return and push. | `$<len>\r\n<elem>\r\n` or `$-1\r\n` | Syntax/arity errors | `BRPOPLPUSH s d 2` &rarr; `$1\r\na\r\n` |
