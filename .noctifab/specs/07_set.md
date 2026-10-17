### 6.5 Set Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `SADD` | `SADD key member [member ...]`<br>Adds members to set. | `:<count_new_members_added>\r\n` | `<2` args errors | `SADD tags db nosql` &rarr; `:2\r\n` |
| `SREM` | `SREM key member [member ...]`<br>Removes members from set. | `:<count_members_removed>\r\n` | `<2` args errors | `SREM tags nosql` &rarr; `:1\r\n` |
| `SMEMBERS` | `SMEMBERS key`<br>Returns all members of set. | `*<count>\r\n$<len>\r\n<m1>...` | `!=1` arg errors | `SMEMBERS tags` &rarr; `*1\r\n$2\r\ndb\r\n` |
| `SISMEMBER` | `SISMEMBER key member`<br>Tests if member is in set. | `:1\r\n` (member)<br>`:0\r\n` (not) | `!=2` args errors | `SISMEMBER tags db` &rarr; `:1\r\n` |
| `SMISMEMBER` | `SMISMEMBER key member [member ...]`<br>Tests multiple members for membership in set. | `*<count>\r\n:1\r\n:0\r\n...` | `<2` args errors | `SMISMEMBER tags db missing` &rarr; `*2\r\n:1\r\n:0\r\n` |
| `SCARD` | `SCARD key`<br>Returns set cardinality (number of members). | `:<count>\r\n` (0 if missing) | `!=1` arg errors | `SCARD tags` &rarr; `:1\r\n` |
| `SUNION` | `SUNION key [key ...]`<br>Returns union of all given sets. | `*<count>\r\n$<len>\r\n<m1>...` | `<1` arg errors | `SUNION s1 s2` &rarr; `*3\r\n$1\r\na\r\n$1\r\nb\r\n$1\r\nc\r\n` |
| `SUNIONSTORE` | `SUNIONSTORE destination key [key ...]`<br>Stores union of sets into destination key. | `:<cardinality_of_dest>\r\n` | `<2` args errors | `SUNIONSTORE s3 s1 s2` &rarr; `:3\r\n` |
| `SINTER` | `SINTER key [key ...]`<br>Returns intersection of given sets. | `*<count>\r\n$<len>\r\n<m1>...` | `<1` arg errors | `SINTER s1 s2` &rarr; `*1\r\n$1\r\nb\r\n` |
| `SINTERSTORE` | `SINTERSTORE destination key [key ...]`<br>Stores intersection into destination. | `:<cardinality_of_dest>\r\n` | `<2` args errors | `SINTERSTORE dest s1 s2` &rarr; `:1\r\n` |
| `SINTERCARD` | `SINTERCARD numkeys key [key ...] [LIMIT limit]`<br>Returns cardinality of intersection. | `:<count>\r\n` | Syntax/arity errors | `SINTERCARD 2 s1 s2` &rarr; `:1\r\n` |
| `SDIFF` | `SDIFF key [key ...]`<br>Returns difference between first set and other sets. | `*<count>\r\n$<len>\r\n<m1>...` | `<1` arg errors | `SDIFF s1 s2` &rarr; `*1\r\n$1\r\na\r\n` |
| `SDIFFSTORE` | `SDIFFSTORE destination key [key ...]`<br>Stores difference into destination. | `:<cardinality_of_dest>\r\n` | `<2` args errors | `SDIFFSTORE dest s1 s2` &rarr; `:1\r\n` |
| `SRANDMEMBER` | `SRANDMEMBER key [count]`<br>Returns random member(s) from set. | `$<len>\r\n<elem>\r\n` or `*<elems>\r\n` | Syntax/arity errors | `SRANDMEMBER tags` &rarr; `$2\r\ndb\r\n` |
| `SPOP` | `SPOP key [count]`<br>Removes and returns random member(s) from set. | `$<len>\r\n<elem>\r\n` or `*<elems>\r\n` | Syntax/arity errors | `SPOP tags` &rarr; `$2\r\ndb\r\n` |
| `SMOVE` | `SMOVE source destination member`<br>Moves member from source to destination. | `:1\r\n` (moved)<br>`:0\r\n` (not found) | `!=3` args errors | `SMOVE s1 s2 a` &rarr; `:1\r\n` |
| `SSCAN` | `SSCAN key cursor [MATCH pattern] [COUNT count]`<br>Incrementally iterates set elements. | `*2\r\n$<len>\r\n<next_cursor>\r\n*<elements>\r\n` | Syntax/arity errors | `SSCAN tags 0` &rarr; `*2\r\n$1\r\n0\r\n*1\r\n$2\r\ndb\r\n` |
