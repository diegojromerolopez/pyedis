### 6.10 Transaction Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `MULTI` | `MULTI`<br>Marks the start of a transaction block. Subsequent commands are queued. | `+OK\r\n` | Nested MULTI: `-ERR MULTI calls can not be nested\r\n` | `MULTI` &rarr; `+OK\r\n` |
| `EXEC` | `EXEC`<br>Executes all queued commands in transaction block atomically. | `*<count>\r\n<reply1>...`<br>`*-1\r\n` (if watched key modified) | Without MULTI: `-ERR EXEC without MULTI\r\n` | `EXEC` &rarr; `*2\r\n+OK\r\n:1\r\n` |
| `DISCARD` | `DISCARD`<br>Flushes all queued commands in transaction and exits transaction state. | `+OK\r\n` | Without MULTI: `-ERR DISCARD without MULTI\r\n` | `DISCARD` &rarr; `+OK\r\n` |
| `WATCH` | `WATCH key [key ...]`<br>Marks keys to be monitored for conditional execution of transaction. | `+OK\r\n` | `<1` arg: `-ERR wrong number of arguments...` | `WATCH balance` &rarr; `+OK\r\n` |
| `UNWATCH` | `UNWATCH`<br>Flushes all watched keys for current connection. | `+OK\r\n` | `!=0` args errors | `UNWATCH` &rarr; `+OK\r\n` |
