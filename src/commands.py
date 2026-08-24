from __future__ import annotations

from src.resp import (
    encode_bulk_string,
    encode_error,
    encode_integer,
    encode_simple_string,
)
from src.store import Store


class CommandDispatcher:
    def __init__(self, store: Store) -> None:
        self.store = store

    async def dispatch(self, args: list[bytes]) -> bytes:
        if not args:
            return encode_error("ERR empty command")

        cmd_str = args[0].decode("utf-8", errors="replace").lower()

        if cmd_str == "get":
            if len(args) != 2:
                return encode_error("ERR wrong number of arguments for 'get' command")
            key = args[1].decode("utf-8")
            val = await self.store.get(key)
            return encode_bulk_string(val)

        elif cmd_str == "set":
            if len(args) < 3:
                return encode_error("ERR wrong number of arguments for 'set' command")
            key = args[1].decode("utf-8")
            val = args[2].decode("utf-8")
            ex: int | float | None = None
            px: int | float | None = None
            nx = False
            xx = False

            i = 3
            while i < len(args):
                opt = args[i].decode("utf-8").upper()
                if opt == "EX" and i + 1 < len(args):
                    try:
                        ex = int(args[i + 1].decode("utf-8"))
                    except ValueError:
                        return encode_error(
                            "ERR value is not an integer or out of range"
                        )
                    i += 2
                elif opt == "PX" and i + 1 < len(args):
                    try:
                        px = int(args[i + 1].decode("utf-8"))
                    except ValueError:
                        return encode_error(
                            "ERR value is not an integer or out of range"
                        )
                    i += 2
                elif opt == "NX":
                    nx = True
                    i += 1
                elif opt == "XX":
                    xx = True
                    i += 1
                else:
                    return encode_error("ERR syntax error")

            success = await self.store.set(key, val, ex=ex, px=px, nx=nx, xx=xx)
            if success:
                return encode_simple_string("OK")
            return encode_bulk_string(None)

        elif cmd_str == "incr":
            if len(args) != 2:
                return encode_error("ERR wrong number of arguments for 'incr' command")
            key = args[1].decode("utf-8")
            num_val, err = await self.store.incr_by(key, 1)
            if err:
                return encode_error(err)
            return encode_integer(num_val if num_val is not None else 0)

        elif cmd_str == "decr":
            if len(args) != 2:
                return encode_error("ERR wrong number of arguments for 'decr' command")
            key = args[1].decode("utf-8")
            num_val, err = await self.store.incr_by(key, -1)
            if err:
                return encode_error(err)
            return encode_integer(num_val if num_val is not None else 0)

        elif cmd_str == "del":
            if len(args) < 2:
                return encode_error("ERR wrong number of arguments for 'del' command")
            keys = [a.decode("utf-8") for a in args[1:]]
            count = await self.store.delete(*keys)
            return encode_integer(count)

        elif cmd_str == "exists":
            if len(args) < 2:
                return encode_error(
                    "ERR wrong number of arguments for 'exists' command"
                )
            keys = [a.decode("utf-8") for a in args[1:]]
            count = await self.store.exists(*keys)
            return encode_integer(count)

        else:
            return encode_error(f"ERR unknown command '{cmd_str}'")

# ---------------------------------------------------------------------------
# MISSING REDIS COMMANDS (not yet implemented)
# ---------------------------------------------------------------------------
# The following commands exist in Redis but are not implemented in pyedis.
# They are listed here as a roadmap for future implementation.
#
# STRING COMMANDS (partially implemented: GET, SET w/ EX/PX/NX/XX, INCR, DECR)
#   APPEND key value
#   GETSET key value              (deprecated in Redis 6.2, use SET+GET)
#   GETEX key [EX|PX|EXAT|PXAT|PERSIST]
#   GETDEL key
#   MGET key [key ...]
#   MSET key value [key value ...]
#   MSETNX key value [key value ...]
#   SETNX key value               (deprecated, use SET NX)
#   SETEX key seconds value       (deprecated, use SET EX)
#   PSETEX key milliseconds value (deprecated, use SET PX)
#   INCRBY key increment
#   INCRBYFLOAT key increment
#   DECRBY key decrement
#   STRLEN key
#   SUBSTR / GETRANGE key start end
#   SETRANGE key offset value
#
# LIST COMMANDS
#   LPUSH key element [element ...]
#   RPUSH key element [element ...]
#   LPUSHX key element [element ...]
#   RPUSHX key element [element ...]
#   LPOP key [count]
#   RPOP key [count]
#   LRANGE key start stop
#   LLEN key
#   LINDEX key index
#   LSET key index element
#   LINSERT key BEFORE|AFTER pivot element
#   LREM key count element
#   LTRIM key start stop
#   LMOVE source destination LEFT|RIGHT LEFT|RIGHT
#   LPOS key element [RANK rank] [COUNT num-matches]
#   BLPOP key [key ...] timeout
#   BRPOP key [key ...] timeout
#
# SET COMMANDS
#   SADD key member [member ...]
#   SREM key member [member ...]
#   SMEMBERS key
#   SISMEMBER key member
#   SMISMEMBER key member [member ...]
#   SCARD key
#   SUNION key [key ...]
#   SUNIONSTORE destination key [key ...]
#   SINTER key [key ...]
#   SINTERSTORE destination key [key ...]
#   SINTERCARD numkeys key [key ...] [LIMIT limit]
#   SDIFF key [key ...]
#   SDIFFSTORE destination key [key ...]
#   SRANDMEMBER key [count]
#   SPOP key [count]
#   SMOVE source destination member
#
# SORTED SET COMMANDS
#   ZADD key [NX|XX] [GT|LT] [CH] [INCR] score member [score member ...]
#   ZRANGE key min max [BYSCORE|BYLEX] [REV] [LIMIT offset count] [WITHSCORES]
#   ZRANGEBYSCORE key min max [WITHSCORES] [LIMIT offset count]
#   ZRANGEBYLEX key min max [LIMIT offset count]
#   ZREVRANGE key start stop [WITHSCORES]
#   ZREVRANGEBYSCORE key max min [WITHSCORES] [LIMIT offset count]
#   ZREVRANGEBYLEX key max min [LIMIT offset count]
#   ZRANK key member [WITHSCORE]
#   ZREVRANK key member [WITHSCORE]
#   ZREM key member [member ...]
#   ZSCORE key member
#   ZMSCORE key member [member ...]
#   ZCARD key
#   ZCOUNT key min max
#   ZLEXCOUNT key min max
#   ZINCRBY key increment member
#   ZUNIONSTORE destination numkeys key [key ...]
#   ZINTERSTORE destination numkeys key [key ...]
#   ZDIFFSTORE destination numkeys key [key ...]
#   ZUNION numkeys key [key ...]
#   ZINTER numkeys key [key ...]
#   ZDIFF numkeys key [key ...]
#   ZPOPMIN key [count]
#   ZPOPMAX key [count]
#   BZPOPMIN key [key ...] timeout
#   BZPOPMAX key [key ...] timeout
#   ZRANDMEMBER key [count [WITHSCORES]]
#   ZRANGESTORE dst src min max [BYSCORE|BYLEX] [REV] [LIMIT offset count]
#
# HASH COMMANDS
#   HSET key field value [field value ...]
#   HGET key field
#   HMSET key field value [field value ...]   (deprecated, use HSET)
#   HMGET key field [field ...]
#   HGETALL key
#   HDEL key field [field ...]
#   HEXISTS key field
#   HKEYS key
#   HVALS key
#   HLEN key
#   HINCRBY key field increment
#   HINCRBYFLOAT key field increment
#   HSETNX key field value
#   HRANDFIELD key [count [WITHVALUES]]
#   HSCAN key cursor [MATCH pattern] [COUNT count]
#
# GENERIC / KEY COMMANDS (partially implemented: DEL, EXISTS)
#   PING [message]
#   ECHO message
#   TYPE key
#   RENAME key newkey
#   RENAMENX key newkey
#   RANDOMKEY
#   KEYS pattern
#   SCAN cursor [MATCH pattern] [COUNT count] [TYPE type]
#   SORT key [BY pattern] [LIMIT offset count] [GET pattern]
#        [ASC|DESC] [ALPHA] [STORE dest]
#   SORT_RO key [BY pattern] [LIMIT offset count] [GET pattern] [ASC|DESC] [ALPHA]
#   EXPIRE key seconds [NX|XX|GT|LT]
#   PEXPIRE key milliseconds [NX|XX|GT|LT]
#   EXPIREAT key unix-time-seconds [NX|XX|GT|LT]
#   PEXPIREAT key unix-time-milliseconds [NX|XX|GT|LT]
#   EXPIRETIME key
#   PEXPIRETIME key
#   TTL key
#   PTTL key
#   PERSIST key
#   COPY source destination [DB destinationdb] [REPLACE]
#   MOVE key db
#   OBJECT ENCODING key
#   OBJECT FREQ key
#   OBJECT HELP
#   OBJECT IDLETIME key
#   OBJECT REFCOUNT key
#   UNLINK key [key ...]
#   WAIT numreplicas timeout
#   DUMP key
#   RESTORE key ttl serialized-value [REPLACE] [ABSTTL]
#           [IDLETIME seconds] [FREQ frequency]
#   MIGRATE host port key|"" destination-db timeout [COPY]
#           [REPLACE] [AUTH password] [KEYS key]
#   OBJECT ENCODING / HELP / FREQ / IDLETIME / REFCOUNT
#
# SERVER / CONNECTION COMMANDS
#   SELECT index
#   DBSIZE
#   FLUSHDB [ASYNC|SYNC]
#   FLUSHALL [ASYNC|SYNC]
#   INFO [section [section ...]]
#   CONFIG GET parameter [parameter ...]
#   CONFIG SET parameter value [parameter value ...]
#   CONFIG RESETSTAT
#   CONFIG REWRITE
#   CLIENT LIST [TYPE normal|master|replica|pubsub] [ID client-id ...]
#   CLIENT ID
#   CLIENT GETNAME
#   CLIENT SETNAME connection-name
#   CLIENT KILL
#   CLIENT NO-EVICT on|off
#   CLIENT PAUSE timeout [WRITE|ALL]
#   CLIENT UNPAUSE
#   CLIENT CACHING yes|no
#   CLIENT REPLY ON|OFF|SKIP
#   CLIENT TRACKINGINFO
#   CLIENT INFO
#   COMMAND [COUNT|DOCS|GETKEYS|INFO|LIST]
#   COMMAND COUNT
#   COMMAND INFO command-name [command-name ...]
#   COMMAND DOCS command-name [command-name ...]
#   COMMAND GETKEYS command [arg ...]
#   COMMAND LIST
#   QUIT
#   RESET
#   AUTH [username] password
#   HELLO [protover [AUTH username password] [SETNAME clientname]]
#   DEBUG SLEEP / DEBUG JMAP / DEBUG SET-ACTIVE-EXPIRE / DEBUG RELOAD / etc.
#   BGSAVE [SCHEDULE]
#   BGREWRITEAOF
#   SAVE
#   LASTSAVE
#   SHUTDOWN [NOSAVE|SAVE] [NOW] [FORCE] [ABORT]
#   SLAVEOF / REPLICAOF host port
#   LOLWUT [VERSION version]
#   LATENCY HISTORY / LATENCY LATEST / LATENCY RESET
#   MEMORY DOCTOR / USAGE / STATS / PURGE / MALLOC-STATS
#   SLOWLOG GET / LEN / RESET
#   MONITOR
#   DEBUG OBJECT key
#
# PUBSUB COMMANDS
#   SUBSCRIBE channel [channel ...]
#   UNSUBSCRIBE [channel [channel ...]]
#   PSUBSCRIBE pattern [pattern ...]
#   PUNSUBSCRIBE [pattern [pattern ...]]
#   PUBLISH channel message
#   PUBSUB CHANNELS / NUMSUB / NUMPAT / SHARDCHANNELS / SHARDNUMSUB
#   SSUBSCRIBE shardchannel [shardchannel ...]
#   SUNSUBSCRIBE [shardchannel [shardchannel ...]]
#   SPUBLISH shardchannel message
#
# TRANSACTION COMMANDS
#   MULTI
#   EXEC
#   DISCARD
#   WATCH key [key ...]
#   UNWATCH
#
# SCRIPTING / FUNCTION COMMANDS
#   EVAL script numkeys [key [key ...]] [arg [arg ...]]
#   EVALSHA sha1 numkeys [key [key ...]] [arg [arg ...]]
#   EVAL_RO script numkeys [key [key ...]] [arg [arg ...]]
#   EVALSHA_RO sha1 numkeys [key [key ...]] [arg [arg ...]]
#   SCRIPT EXISTS sha1 [sha1 ...]
#   SCRIPT FLUSH [ASYNC|SYNC]
#   SCRIPT LOAD script
#   SCRIPT DEBUG YES|SYNC|NO
#   FCALL function numkeys [key [key ...]] [arg [arg ...]]
#   FCALL_RO function numkeys [key [key ...]] [arg [arg ...]]
#   FUNCTION LIST [LIBRARYNAME library-name-pattern] [WITHCODE]
#   FUNCTION LOAD [REPLACE] function-code
#   FUNCTION DELETE library-name
#   FUNCTION DUMP
#   FUNCTION RESTORE serialized-value [FLUSH|APPEND|REPLACE]
#   FUNCTION STATS
#   FUNCTION FLUSH [ASYNC|SYNC]
#
# STREAM COMMANDS
#   XADD key [NOMKSTREAM] [MAXLEN|MINID [=|~] threshold [LIMIT count]]
#        *|id field value [field value ...]
#   XREAD [COUNT count] [BLOCK milliseconds] STREAMS key [key ...] id [id ...]
#   XRANGE key start end [COUNT count]
#   XREVRANGE key end start [COUNT count]
#   XLEN key
#   XTRIM key MAXLEN|MINID [=|~] threshold [LIMIT count]
#   XDEL key id [id ...]
#   XINFO STREAM / GROUPS / CONSUMERS / FULL
#   XGROUP CREATE / CREATECONSUMER / DELCONSUMER / DESTROY / SETID
#   XREADGROUP GROUP group consumer [COUNT count] [BLOCK milliseconds]
#              [NOACK] STREAMS key [key ...] id [id ...]
#   XACK key group id [id ...]
#   XCLAIM key group consumer min-idle-time id [id ...]
#   XAUTOCLAIM key group consumer min-idle-time start [COUNT count] [JUSTID]
#   XPENDING key group [[IDLE min-idle-time] start end count [consumer]]
# ---------------------------------------------------------------------------
