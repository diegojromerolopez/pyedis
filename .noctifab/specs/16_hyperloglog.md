### 6.14 HyperLogLog Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `PFADD` | `PFADD key element [element ...]`<br>Adds elements to the HyperLogLog probabilistic data structure. | `:1\r\n` (if internal register modified)<br>`:0\r\n` (if not modified) | `<2` args: `-ERR wrong number of arguments...`<br>Wrong Type: `-WRONGTYPE ...` | `PFADD visitors "user_1" "user_2"` &rarr; `:1\r\n`<br>`PFADD visitors "user_1"` &rarr; `:0\r\n` |
| `PFCOUNT` | `PFCOUNT key [key ...]`<br>Returns approximated cardinality of set(s) observed by HyperLogLog. | `:<approx_cardinality>\r\n` | `<1` arg: `-ERR wrong number of arguments...`<br>Wrong Type: `-WRONGTYPE ...` | `PFCOUNT visitors` &rarr; `:2\r\n`<br>`PFCOUNT hll1 hll2` &rarr; `:150\r\n` |
| `PFMERGE` | `PFMERGE destkey sourcekey [sourcekey ...]`<br>Merges multiple HyperLogLogs into destination key. | `+OK\r\n` | `<2` args: `-ERR wrong number of arguments...`<br>Wrong Type: `-WRONGTYPE ...` | `PFMERGE all_visitors v_mon v_tue` &rarr; `+OK\r\n` |
