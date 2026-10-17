### 6.4 Hash Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `HSET` | `HSET key field value [field value ...]`<br>Sets field-value pairs in hash. | `:<count_new_fields_added>\r\n` | Odd arguments errors | `HSET user name "Ada" age "30"` &rarr; `:2\r\n` |
| `HGET` | `HGET key field`<br>Returns value of hash field. | `$<len>\r\n<val>\r\n` or `$-1\r\n` | `!=2` args errors | `HGET user name` &rarr; `$3\r\nAda\r\n` |
| `HMSET` | `HMSET key field value [field value ...]`<br>Sets multiple hash fields (alias for HSET). | `+OK\r\n` | Odd arguments errors | `HMSET user k1 v1` &rarr; `+OK\r\n` |
| `HMGET` | `HMGET key field [field ...]`<br>Returns values for specified fields. | `*<count>\r\n$<len>\r\n<v1>\r\n...` | `<2` args errors | `HMGET user name age missing` &rarr; `*3\r\n$3\r\nAda\r\n$2\r\n30\r\n$-1\r\n` |
| `HGETALL` | `HGETALL key`<br>Returns all fields and values in hash. | `*<2*count>\r\n$<len>\r\n<f1>\r\n$<len>\r\n<v1>...` | `!=1` arg errors | `HGETALL user` &rarr; `*4\r\n$4\r\nname\r\n$3\r\nAda\r\n$3\r\nage\r\n$2\r\n30\r\n` |
| `HDEL` | `HDEL key field [field ...]`<br>Deletes one or more hash fields. | `:<count_fields_removed>\r\n` | `<2` args errors | `HDEL user age` &rarr; `:1\r\n` |
| `HEXISTS` | `HEXISTS key field`<br>Determines if a hash field exists. | `:1\r\n` (exists)<br>`:0\r\n` (missing) | `!=2` args errors | `HEXISTS user name` &rarr; `:1\r\n` |
| `HKEYS` | `HKEYS key`<br>Returns all field names in hash. | `*<count>\r\n$<len>\r\n<f1>...` | `!=1` arg errors | `HKEYS user` &rarr; `*1\r\n$4\r\nname\r\n` |
| `HVALS` | `HVALS key`<br>Returns all values in hash. | `*<count>\r\n$<len>\r\n<v1>...` | `!=1` arg errors | `HVALS user` &rarr; `*1\r\n$3\r\nAda\r\n` |
| `HLEN` | `HLEN key`<br>Returns number of fields contained in hash. | `:<number_of_fields>\r\n` | `!=1` arg errors | `HLEN user` &rarr; `:1\r\n` |
| `HINCRBY` | `HINCRBY key field increment`<br>Increments integer value of hash field. | `:<new_int_value>\r\n` | Non-integer errors | `HINCRBY user visits 1` &rarr; `:1\r\n` |
| `HINCRBYFLOAT` | `HINCRBYFLOAT key field increment`<br>Increments float value of hash field. | `$<len>\r\n<new_float_str>\r\n` | Non-float errors | `HINCRBYFLOAT user rate 0.5` &rarr; `$3\r\n1.5\r\n` |
| `HSETNX` | `HSETNX key field value`<br>Sets field value only if field does not exist. | `:1\r\n` (set)<br>`:0\r\n` (not set) | `!=3` args errors | `HSETNX user email "a@b.c"` &rarr; `:1\r\n` |
| `HRANDFIELD` | `HRANDFIELD key [count [WITHVALUES]]`<br>Returns random field(s) from hash. | `$<len>\r\n<field>\r\n` or `*<fields_or_pairs>\r\n` | Syntax/arity errors | `HRANDFIELD user 1` &rarr; `*1\r\n$4\r\nname\r\n` |
| `HSCAN` | `HSCAN key cursor [MATCH pattern] [COUNT count]`<br>Incrementally iterates hash fields and values. | `*2\r\n$<len>\r\n<next_cursor>\r\n*<field_val_array>\r\n` | Syntax/arity errors | `HSCAN user 0` &rarr; `*2\r\n$1\r\n0\r\n*2\r\n$4\r\nname\r\n$3\r\nAda\r\n` |
| `HSTRLEN` | `HSTRLEN key field`<br>Returns length of value string associated with field. | `:<len>\r\n` (0 if missing) | `!=2` args errors | `HSTRLEN user name` &rarr; `:3\r\n` |
