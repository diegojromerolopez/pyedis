### 6.8 Generic & Key Management Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `COPY` | `COPY source destination [DB destination-db] [REPLACE]`<br>Copies value from source to destination. | `:1\r\n` (copied)<br>`:0\r\n` (not copied) | Syntax/arity errors | `COPY k1 k2 REPLACE` &rarr; `:1\r\n` |
| `DEL` | `DEL key [key ...]`<br>Removes specified key(s). | `:<count_removed>\r\n` | `<1` arg errors | `DEL k1 k2` &rarr; `:2\r\n` |
| `DUMP` | `DUMP key`<br>Returns serialized value stored at key. | `$<len>\r\n<bytes>\r\n` or `$-1\r\n` | `!=1` arg errors | `DUMP k` &rarr; `$10\r\n\x00\xc0\n\t...` |
| `EXISTS` | `EXISTS key [key ...]`<br>Returns count of existing keys. | `:<count_existing>\r\n` | `<1` arg errors | `EXISTS k1 k2` &rarr; `:1\r\n` |
| `EXPIRE` | `EXPIRE key seconds [NX\|XX\|GT\|LT]`<br>Sets expiration timeout in seconds. | `:1\r\n` (set)<br>`:0\r\n` (not set) | Invalid integer errors | `EXPIRE k 60` &rarr; `:1\r\n` |
| `EXPIREAT` | `EXPIREAT key unix-time-seconds [NX\|XX\|GT\|LT]`<br>Sets expiration at absolute Unix timestamp. | `:1\r\n` (set)<br>`:0\r\n` (not set) | Invalid timestamp errors | `EXPIREAT k 1893456000` &rarr; `:1\r\n` |
| `EXPIRETIME` | `EXPIRETIME key`<br>Returns absolute Unix expiration timestamp in seconds. | `:<timestamp>\r\n` (-1 no TTL, -2 missing) | `!=1` arg errors | `EXPIRETIME k` &rarr; `:1893456000\r\n` |
| `KEYS` | `KEYS pattern`<br>Returns all keys matching glob pattern (`*`, `?`, `[abc]`, `\*`). | `*<count>\r\n$<len>\r\n<k1>...` | `!=1` arg errors | `KEYS user:*` &rarr; `*1\r\n$6\r\nuser:1\r\n` |
| `MIGRATE` | `MIGRATE host port key\|"" dest-db timeout [COPY] [REPLACE] [AUTH pwd] [KEYS k ...]` | `+OK\r\n` or `+NOKEY\r\n` | Connection/syntax errors | `MIGRATE 127.0.0.1 6380 k 0 5000 COPY` &rarr; `+OK\r\n` |
| `MOVE` | `MOVE key db`<br>Moves key to another database index. | `:1\r\n` (moved)<br>`:0\r\n` (not moved) | `!=2` args errors | `MOVE k 1` &rarr; `:1\r\n` |
| `OBJECT` | `OBJECT ENCODING\|FREQ\|HELP\|IDLETIME\|REFCOUNT key`<br>Inspects object internals. | `$<len>\r\n<encoding>\r\n` or `:<int>\r\n` | Syntax errors | `OBJECT ENCODING k` &rarr; `$3\r\nraw\r\n` |
| `PERSIST` | `PERSIST key`<br>Removes existing timeout on key, making it persistent. | `:1\r\n` (cleared)<br>`:0\r\n` (no TTL/missing) | `!=1` arg errors | `PERSIST k` &rarr; `:1\r\n` |
| `PEXPIRE` | `PEXPIRE key milliseconds [NX\|XX\|GT\|LT]`<br>Sets expiration in milliseconds. | `:1\r\n` (set)<br>`:0\r\n` (not set) | Invalid integer errors | `PEXPIRE k 5000` &rarr; `:1\r\n` |
| `PEXPIREAT` | `PEXPIREAT key unix-time-milliseconds [NX\|XX\|GT\|LT]`<br>Sets expiration timestamp in ms. | `:1\r\n` (set)<br>`:0\r\n` (not set) | Invalid integer errors | `PEXPIREAT k 1893456000000` &rarr; `:1\r\n` |
| `PEXPIRETIME` | `PEXPIRETIME key`<br>Returns absolute Unix expiration timestamp in milliseconds. | `:<ms_timestamp>\r\n` (-1 no TTL, -2 missing) | `!=1` arg errors | `PEXPIRETIME k` &rarr; `:1893456000000\r\n` |
| `PTTL` | `PTTL key`<br>Returns remaining TTL in milliseconds. | `:-2\r\n` (missing), `:-1\r\n` (no TTL), or `:<ms>\r\n` | `!=1` arg errors | `PTTL k` &rarr; `:4800\r\n` |
| `RANDOMKEY` | `RANDOMKEY`<br>Returns a random existing key from database. | `$<len>\r\n<key>\r\n` (or `$-1\r\n` if empty) | `!=0` args errors | `RANDOMKEY` &rarr; `$4\r\nuser\r\n` |
| `RENAME` | `RENAME key newkey`<br>Renames key to newkey, overwriting existing newkey. | `+OK\r\n` | Missing key: `-ERR no such key\r\n` | `RENAME old new` &rarr; `+OK\r\n` |
| `RENAMENX` | `RENAMENX key newkey`<br>Renames key to newkey only if newkey does not exist. | `:1\r\n` (renamed)<br>`:0\r\n` (newkey exists) | Missing key: `-ERR no such key\r\n` | `RENAMENX old new` &rarr; `:1\r\n` |
| `RESTORE` | `RESTORE key ttl serialized-value [REPLACE] [ABSTTL] [IDLETIME s] [FREQ f]` | `+OK\r\n` | Target exists / syntax errors | `RESTORE k 0 "\x00\xc0..." REPLACE` &rarr; `+OK\r\n` |
| `SCAN` | `SCAN cursor [MATCH pattern] [COUNT count] [TYPE type]`<br>Incrementally iterates keys. | `*2\r\n$<len>\r\n<next_cursor>\r\n*<keys_array>\r\n` | Syntax/cursor errors | `SCAN 0 MATCH user:*` &rarr; `*2\r\n$1\r\n0\r\n*1\r\n$6\r\nuser:1\r\n` |
| `SORT` | `SORT key [BY pattern] [LIMIT off count] [GET pat ...] [ASC\|DESC] [ALPHA] [STORE dst]` | `*<elements>\r\n` (or `:<count_stored>\r\n` if STORE) | Syntax/type errors | `SORT list ALPHA` &rarr; `*2\r\n$1\r\na\r\n$1\r\nb\r\n` |
| `SORT_RO` | `SORT_RO key [BY pattern] [LIMIT off count] [GET pat ...] [ASC\|DESC] [ALPHA]` | `*<elements>\r\n` | Read-only sort syntax errors | `SORT_RO list ALPHA` &rarr; `*2\r\n$1\r\na\r\n$1\r\nb\r\n` |
| `TOUCH` | `TOUCH key [key ...]`<br>Alters last access time of key(s). | `:<count_keys_touched>\r\n` | `<1` arg errors | `TOUCH k1 k2` &rarr; `:2\r\n` |
| `TTL` | `TTL key`<br>Returns remaining TTL in seconds. | `:-2\r\n` (missing), `:-1\r\n` (no TTL), or `:<seconds>\r\n` | `!=1` arg errors | `TTL k` &rarr; `:58\r\n` |
| `TYPE` | `TYPE key`<br>Returns string representation of key data type. | `+string\r\n`, `+list\r\n`, `+set\r\n`, `+zset\r\n`, `+hash\r\n`, `+stream\r\n`, `+none\r\n` | `!=1` arg errors | `TYPE k` &rarr; `+string\r\n` |
| `UNLINK` | `UNLINK key [key ...]`<br>Asynchronously deletes key(s). | `:<count_keys_unlinked>\r\n` | `<1` arg errors | `UNLINK k1 k2` &rarr; `:2\r\n` |
| `WAIT` | `WAIT numreplicas timeout`<br>Blocks until writes reach replicas. | `:<numreplicas_reached>\r\n` | Arity/integer errors | `WAIT 1 1000` &rarr; `:1\r\n` |
| `WAITAOF` | `WAITAOF numlocal numreplicas timeout`<br>Blocks until previous writes are synced to local AOF and replicas. | `*2\r\n:<numlocal_synced>\r\n:<numreplicas_synced>\r\n` | Arity/integer errors | `WAITAOF 1 0 1000` &rarr; `*2\r\n:1\r\n:0\r\n` |
