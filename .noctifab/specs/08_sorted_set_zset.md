### 6.6 Sorted Set (ZSet) Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `ZADD` | `ZADD key [NX\|XX] [GT\|LT] [CH] [INCR] score member [score member ...]`<br>Adds/updates scored members. | `:<count_added_or_changed>\r\n` (or float bulk if INCR) | Syntax/type errors | `ZADD lb 100 "alice" 90 "bob"` &rarr; `:2\r\n` |
| `ZCARD` | `ZCARD key`<br>Returns sorted set cardinality. | `:<count>\r\n` (0 if missing) | `!=1` arg errors | `ZCARD lb` &rarr; `:2\r\n` |
| `ZCOUNT` | `ZCOUNT key min max`<br>Counts members with scores in [min, max] range. | `:<count>\r\n` | `!=3` args errors | `ZCOUNT lb 90 100` &rarr; `:2\r\n` |
| `ZDIFF` | `ZDIFF numkeys key [key ...] [WITHSCORES]`<br>Computes difference of sorted sets. | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZDIFF 2 z1 z2` &rarr; `*1\r\n$1\r\na\r\n` |
| `ZDIFFSTORE` | `ZDIFFSTORE destination numkeys key [key ...]`<br>Stores difference into destination. | `:<cardinality_of_dest>\r\n` | Syntax/arity errors | `ZDIFFSTORE out 2 z1 z2` &rarr; `:1\r\n` |
| `ZINCRBY` | `ZINCRBY key increment member`<br>Increments score of member in sorted set. | `$<len>\r\n<new_score_str>\r\n` | Non-float score errors | `ZINCRBY lb 10 "bob"` &rarr; `$3\r\n100\r\n` |
| `ZINTER` | `ZINTER numkeys key [key ...] [WEIGHTS w ...] [AGGREGATE SUM\|MIN\|MAX] [WITHSCORES]` | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZINTER 2 z1 z2` &rarr; `*1\r\n$1\r\nb\r\n` |
| `ZINTERCARD` | `ZINTERCARD numkeys key [key ...] [LIMIT limit]`<br>Returns cardinality of intersection. | `:<count>\r\n` | Syntax/arity errors | `ZINTERCARD 2 z1 z2` &rarr; `:1\r\n` |
| `ZINTERSTORE` | `ZINTERSTORE destination numkeys key [key ...] [WEIGHTS w ...] [AGGREGATE SUM\|MIN\|MAX]` | `:<cardinality_of_dest>\r\n` | Syntax/arity errors | `ZINTERSTORE out 2 z1 z2` &rarr; `:1\r\n` |
| `ZLEXCOUNT` | `ZLEXCOUNT key min max`<br>Counts members between lexicographical bounds. | `:<count>\r\n` | Syntax/arity errors | `ZLEXCOUNT z [a [z` &rarr; `:2\r\n` |
| `ZMSCORE` | `ZMSCORE key member [member ...]`<br>Returns scores for specified members. | `*<count>\r\n$<len>\r\n<score>\r\n...` | `<2` args errors | `ZMSCORE lb alice missing` &rarr; `*2\r\n$3\r\n100\r\n$-1\r\n` |
| `ZPOPMAX` | `ZPOPMAX key [count]`<br>Removes and returns members with highest scores. | `*<2*count>\r\n$<len>\r\n<m>\r\n$<len>\r\n<s>...` | Syntax/arity errors | `ZPOPMAX lb 1` &rarr; `*2\r\n$5\r\nalice\r\n$3\r\n100\r\n` |
| `ZPOPMIN` | `ZPOPMIN key [count]`<br>Removes and returns members with lowest scores. | `*<2*count>\r\n$<len>\r\n<m>\r\n$<len>\r\n<s>...` | Syntax/arity errors | `ZPOPMIN lb 1` &rarr; `*2\r\n$3\r\nbob\r\n$2\r\n90\r\n` |
| `ZRANDMEMBER` | `ZRANDMEMBER key [count [WITHSCORES]]`<br>Returns random member(s) from sorted set. | `$<len>\r\n<m>\r\n` or `*<members>\r\n` | Syntax/arity errors | `ZRANDMEMBER lb` &rarr; `$5\r\nalice\r\n` |
| `ZRANGE` | `ZRANGE key min max [BYSCORE\|BYLEX] [REV] [LIMIT off count] [WITHSCORES]` | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZRANGE lb 0 -1 WITHSCORES` &rarr; `*4\r\n$3\r\nbob\r\n$2\r\n90\r\n$5\r\nalice\r\n$3\r\n100\r\n` |
| `ZRANGEBYSCORE` | `ZRANGEBYSCORE key min max [WITHSCORES] [LIMIT offset count]`<br>Queries members by score range. | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZRANGEBYSCORE lb 90 100` &rarr; `*2\r\n$3\r\nbob\r\n$5\r\nalice\r\n` |
| `ZRANGEBYLEX` | `ZRANGEBYLEX key min max [LIMIT offset count]`<br>Queries members by lexicographical range. | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZRANGEBYLEX z [a [z` &rarr; `*2\r\n$1\r\na\r\n$1\r\nb\r\n` |
| `ZRANGESTORE` | `ZRANGESTORE dst src min max [BYSCORE\|BYLEX] [REV] [LIMIT offset count]` | `:<cardinality_stored>\r\n` | Syntax/arity errors | `ZRANGESTORE out lb 0 1` &rarr; `:2\r\n` |
| `ZRANK` | `ZRANK key member [WITHSCORE]`<br>Returns 0-based rank from lowest to highest score. | `:<rank>\r\n` (or `$-1\r\n`) | `!=2` and `!=3` args errors | `ZRANK lb bob` &rarr; `:0\r\n` |
| `ZREM` | `ZREM key member [member ...]`<br>Removes members from sorted set. | `:<count_removed>\r\n` | `<2` args errors | `ZREM lb bob` &rarr; `:1\r\n` |
| `ZREMRANGEBYLEX` | `ZREMRANGEBYLEX key min max`<br>Removes members in lexicographical range. | `:<count_removed>\r\n` | `!=3` args errors | `ZREMRANGEBYLEX z [a [c` &rarr; `:2\r\n` |
| `ZREMRANGEBYRANK` | `ZREMRANGEBYRANK key start stop`<br>Removes members within rank range. | `:<count_removed>\r\n` | `!=3` args errors | `ZREMRANGEBYRANK lb 0 0` &rarr; `:1\r\n` |
| `ZREMRANGEBYSCORE` | `ZREMRANGEBYSCORE key min max`<br>Removes members within score range. | `:<count_removed>\r\n` | `!=3` args errors | `ZREMRANGEBYSCORE lb 0 50` &rarr; `:0\r\n` |
| `ZREVRANGE` | `ZREVRANGE key start stop [WITHSCORES]`<br>Returns members highest to lowest score. | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZREVRANGE lb 0 -1` &rarr; `*2\r\n$5\r\nalice\r\n$3\r\nbob\r\n` |
| `ZREVRANGEBYLEX` | `ZREVRANGEBYLEX key max min [LIMIT offset count]`<br>Reverse lexicographical query. | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZREVRANGEBYLEX z [z [a` &rarr; `*2\r\n$1\r\nb\r\n$1\r\na\r\n` |
| `ZREVRANGEBYSCORE` | `ZREVRANGEBYSCORE key max min [WITHSCORES] [LIMIT offset count]`<br>Reverse score query. | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZREVRANGEBYSCORE lb 100 90` &rarr; `*2\r\n$5\r\nalice\r\n$3\r\nbob\r\n` |
| `ZREVRANK` | `ZREVRANK key member [WITHSCORE]`<br>Returns rank from highest to lowest score. | `:<rank>\r\n` (or `$-1\r\n`) | Syntax/arity errors | `ZREVRANK lb alice` &rarr; `:0\r\n` |
| `ZSCAN` | `ZSCAN key cursor [MATCH pattern] [COUNT count]`<br>Incrementally iterates sorted set elements. | `*2\r\n$<len>\r\n<next_cursor>\r\n*<elem_scores>\r\n` | Syntax/arity errors | `ZSCAN lb 0` &rarr; `*2\r\n$1\r\n0\r\n*4\r\n$3\r\nbob\r\n$2\r\n90\r\n$5\r\nalice\r\n$3\r\n100\r\n` |
| `ZSCORE` | `ZSCORE key member`<br>Returns score of member. | `$<len>\r\n<score_str>\r\n` or `$-1\r\n` | `!=2` args errors | `ZSCORE lb alice` &rarr; `$3\r\n100\r\n` |
| `ZUNION` | `ZUNION numkeys key [key ...] [WEIGHTS w ...] [AGGREGATE SUM\|MIN\|MAX] [WITHSCORES]` | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZUNION 2 z1 z2` &rarr; `*3\r\n$1\r\na\r\n$1\r\nb\r\n$1\r\nc\r\n` |
| `ZUNIONSTORE` | `ZUNIONSTORE destination numkeys key [key ...] [WEIGHTS w ...] [AGGREGATE SUM\|MIN\|MAX]` | `:<cardinality_of_dest>\r\n` | Syntax/arity errors | `ZUNIONSTORE out 2 z1 z2` &rarr; `:3\r\n` |
| `BZPOPMIN` | `BZPOPMIN key [key ...] timeout`<br>Blocking pop member with lowest score. | `*3\r\n$<len>\r\n<k>\r\n$<len>\r\n<m>\r\n$<len>\r\n<s>\r\n` or `*-1\r\n` | Arity/timeout errors | `BZPOPMIN lb 1` &rarr; `*3\r\n$2\r\nlb\r\n$3\r\nbob\r\n$2\r\n90\r\n` |
| `BZPOPMAX` | `BZPOPMAX key [key ...] timeout`<br>Blocking pop member with highest score. | `*3\r\n$<len>\r\n<k>\r\n$<len>\r\n<m>\r\n$<len>\r\n<s>\r\n` or `*-1\r\n` | Arity/timeout errors | `BZPOPMAX lb 1` &rarr; `*3\r\n$2\r\nlb\r\n$5\r\nalice\r\n$3\r\n100\r\n` |
