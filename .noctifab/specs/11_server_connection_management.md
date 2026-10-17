### 6.9 Server & Connection Management Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `AUTH` | `AUTH [username] password`<br>Authenticates connection. | `+OK\r\n` | Invalid password errors | `AUTH secretpass` &rarr; `+OK\r\n` |
| `BGREWRITEAOF` | `BGREWRITEAOF`<br>Triggers background AOF rewrite/compaction. | `+Background append only file rewriting started\r\n` | None | `BGREWRITEAOF` &rarr; `+Background append only file rewriting started\r\n` |
| `BGSAVE` | `BGSAVE [SCHEDULE]`<br>Asynchronously saves database state to disk. | `+Background saving started\r\n` | None | `BGSAVE` &rarr; `+Background saving started\r\n` |
| `CLIENT` | `CLIENT LIST\|ID\|GETNAME\|SETNAME\|KILL\|NO-EVICT\|PAUSE\|REPLY\|TRACKING\|INFO` | Subcommand-specific RESP response (`+OK`, strings, arrays) | Syntax/subcommand errors | `CLIENT SETNAME myapp` &rarr; `+OK\r\n`<br>`CLIENT ID` &rarr; `:42\r\n` |
| `COMMAND` | `COMMAND [COUNT\|DOCS\|GETKEYS\|INFO\|LIST]`<br>Returns driver command metadata. | `*<commands_array>\r\n` or command details | None | `COMMAND COUNT` &rarr; `:217\r\n` |
| `CONFIG` | `CONFIG GET\|SET\|RESETSTAT\|REWRITE parameter [value]`<br>Manages configuration. | `*<key_value_pairs>\r\n` or `+OK\r\n` | Syntax/parameter errors | `CONFIG GET maxmemory` &rarr; `*2\r\n$9\r\nmaxmemory\r\n$1\r\n0\r\n` |
| `DBSIZE` | `DBSIZE`<br>Returns total key count in currently selected database. | `:<key_count>\r\n` | `!=0` args errors | `DBSIZE` &rarr; `:150\r\n` |
| `ECHO` | `ECHO message`<br>Echoes message back to client. | `$<len>\r\n<message>\r\n` | `!=1` arg errors | `ECHO "hello"` &rarr; `$5\r\nhello\r\n` |
| `FLUSHALL` | `FLUSHALL [ASYNC\|SYNC]`<br>Deletes all keys from all databases and truncates AOF. | `+OK\r\n` | Syntax errors | `FLUSHALL` &rarr; `+OK\r\n` |
| `FLUSHDB` | `FLUSHDB [ASYNC\|SYNC]`<br>Deletes all keys from currently selected database. | `+OK\r\n` | Syntax errors | `FLUSHDB` &rarr; `+OK\r\n` |
| `HELLO` | `HELLO [protover [AUTH user pwd] [SETNAME name]]`<br>Handshake & switches RESP2/RESP3. | `*<server_info_map_or_array>\r\n` | Version/auth errors | `HELLO 3` &rarr; `*14\r\n$6\r\nserver\r\n$7\r\npyedis...` |
| `INFO` | `INFO [section [section ...]]`<br>Returns server statistics and information. | `$<len>\r\n<info_string>\r\n` | None | `INFO server` &rarr; `$45\r\n# Server\r\npyedis_version:1.0.0...` |
| `LASTSAVE` | `LASTSAVE`<br>Returns Unix timestamp of last successful save to disk. | `:<unix_timestamp>\r\n` | `!=0` args errors | `LASTSAVE` &rarr; `:1724623200\r\n` |
| `LATENCY` | `LATENCY DOCTOR\|GRAPH\|HISTORY\|LATEST\|RESET [event]` | Latency reports or `+OK\r\n` | Subcommand errors | `LATENCY LATEST` &rarr; `*0\r\n` |
| `LOLWUT` | `LOLWUT [VERSION version]`<br>Renders computer art piece. | `$<len>\r\n<art_string>\r\n` | None | `LOLWUT` &rarr; `$32\r\npyedis: Redis ver. 7 compatible\r\n` |
| `MEMORY` | `MEMORY DOCTOR\|MALLOC-STATS\|PURGE\|STATS\|USAGE key [SAMPLES count]` | Memory report or integer bytes | Subcommand errors | `MEMORY USAGE k` &rarr; `:64\r\n` |
| `MONITOR` | `MONITOR`<br>Streams back all commands processed by server in real time. | `+OK\r\n` (enters streaming mode) | None | `MONITOR` &rarr; `+OK\r\n` |
| `PING` | `PING [message]`<br>Tests connection liveness. | 0 args: `+PONG\r\n`<br>1 arg: `$<len>\r\n<msg>\r\n` | `>1` args errors | `PING` &rarr; `+PONG\r\n`<br>`PING "hi"` &rarr; `$2\r\nhi\r\n` |
| `QUIT` | `QUIT`<br>Closes connection. | `+OK\r\n` (closes TCP connection) | `!=0` args errors | `QUIT` &rarr; `+OK\r\n` |
| `REPLICAOF` | `REPLICAOF host port` / `REPLICAOF NO ONE`<br>Configures server replication target (or standalone master). | `+OK\r\n` | Arity/port errors | `REPLICAOF NO ONE` &rarr; `+OK\r\n` |
| `RESET` | `RESET`<br>Resets connection state (watches, subscriptions, transactions). | `+RESET\r\n` | `!=0` args errors | `RESET` &rarr; `+RESET\r\n` |
| `ROLE` | `ROLE`<br>Returns replication role of instance. | `*3\r\n$6\r\nmaster\r\n:0\r\n*0\r\n` | `!=0` args errors | `ROLE` &rarr; `*3\r\n$6\r\nmaster\r\n:0\r\n*0\r\n` |
| `SAVE` | `SAVE`<br>Synchronously saves database to disk. | `+OK\r\n` | None | `SAVE` &rarr; `+OK\r\n` |
| `SELECT` | `SELECT index`<br>Changes selected database (0-15). | `+OK\r\n` | Invalid index errors | `SELECT 1` &rarr; `+OK\r\n` |
| `SHUTDOWN` | `SHUTDOWN [NOSAVE\|SAVE] [NOW] [FORCE] [ABORT]`<br>Shuts down server gracefully. | Server flushes and exits 0 | None | `SHUTDOWN` &rarr; (terminates process) |
| `SLAVEOF` | `SLAVEOF host port` / `SLAVEOF NO ONE`<br>Legacy alias for `REPLICAOF`. | `+OK\r\n` | Arity/port errors | `SLAVEOF NO ONE` &rarr; `+OK\r\n` |
| `SLOWLOG` | `SLOWLOG GET [count]\|LEN\|RESET`<br>Manages slow query log. | `*<slowlog_entries>\r\n` or `:<count>\r\n` or `+OK\r\n` | Subcommand errors | `SLOWLOG LEN` &rarr; `:0\r\n` |
| `TIME` | `TIME`<br>Returns current server time as `[unix_seconds_str, microseconds_str]`. | `*2\r\n$<len>\r\n<sec>\r\n$<len>\r\n<usec>\r\n` | `!=0` args errors | `TIME` &rarr; `*2\r\n$10\r\n1724623200\r\n$6\r\n123456\r\n` |
