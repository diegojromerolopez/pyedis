### 6.12 Scripting & Function Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `EVAL` | `EVAL script numkeys [key [key ...]] [arg [arg ...]]`<br>Executes Lua script on server. | Result of script mapped to RESP | Script execution errors: `-ERR Error running script...` | `EVAL "return redis.call('GET', KEYS[1])" 1 k` &rarr; `$3\r\nval\r\n` |
| `EVALSHA` | `EVALSHA sha1 numkeys [key [key ...]] [arg [arg ...]]`<br>Executes cached script by SHA1. | Result of script mapped to RESP | Missing script: `-NOSCRIPT No matching script...` | `EVALSHA <sha1> 1 k` &rarr; `$3\r\nval\r\n` |
| `EVAL_RO` | `EVAL_RO script numkeys [key [key ...]] [arg [arg ...]]`<br>Read-only script execution. | Result of script | Mutation attempt in RO mode errors | `EVAL_RO "return 42" 0` &rarr; `:42\r\n` |
| `EVALSHA_RO` | `EVALSHA_RO sha1 numkeys [key [key ...]] [arg [arg ...]]`<br>Read-only cached script. | Result of script | Missing script / mutation errors | `EVALSHA_RO <sha1> 0` &rarr; `:42\r\n` |
| `SCRIPT` | `SCRIPT EXISTS\|FLUSH\|LOAD\|KILL\|DEBUG [args]`<br>Manages script cache. | `*<1_or_0_array>\r\n` or `$<len>\r\n<sha1>\r\n` or `+OK\r\n` | Syntax/subcommand errors | `SCRIPT LOAD "return 1"` &rarr; `$40\r\ne0e1f9...` |
| `FCALL` | `FCALL function numkeys [key [key ...]] [arg [arg ...]]`<br>Invokes stored function. | Result of function mapped to RESP | Function error / not found errors | `FCALL myfunc 1 k arg1` &rarr; `+OK\r\n` |
| `FCALL_RO` | `FCALL_RO function numkeys [key [key ...]] [arg [arg ...]]`<br>Read-only function call. | Result of function | Mutation attempt in RO mode errors | `FCALL_RO myfunc 1 k arg1` &rarr; `+OK\r\n` |
| `FUNCTION` | `FUNCTION LOAD\|DELETE\|LIST\|STATS\|DUMP\|RESTORE\|FLUSH [args]` | Subcommand-specific status / library arrays | Syntax/subcommand errors | `FUNCTION LIST` &rarr; `*0\r\n` |
