### 6.11 Pub/Sub Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `SUBSCRIBE` | `SUBSCRIBE channel [channel ...]`<br>Subscribes client to specified channels. | `*3\r\n$9\r\nsubscribe\r\n$<len>\r\n<chan>\r\n:<sub_count>\r\n` | `<1` arg errors | `SUBSCRIBE news` &rarr; `*3\r\n$9\r\nsubscribe\r\n$4\r\nnews\r\n:1\r\n` |
| `UNSUBSCRIBE` | `UNSUBSCRIBE [channel [channel ...]]`<br>Unsubscribes client from channels. | `*3\r\n$11\r\nunsubscribe\r\n$<len>\r\n<chan>\r\n:<sub_count>\r\n` | None | `UNSUBSCRIBE news` &rarr; `*3\r\n$11\r\nunsubscribe\r\n$4\r\nnews\r\n:0\r\n` |
| `PSUBSCRIBE` | `PSUBSCRIBE pattern [pattern ...]`<br>Subscribes client to glob patterns. | `*3\r\n$10\r\npsubscribe\r\n$<len>\r\n<pattern>\r\n:<sub_count>\r\n` | `<1` arg errors | `PSUBSCRIBE news.*` &rarr; `*3\r\n$10\r\npsubscribe\r\n$6\r\nnews.*\r\n:1\r\n` |
| `PUNSUBSCRIBE` | `PUNSUBSCRIBE [pattern [pattern ...]]`<br>Unsubscribes client from patterns. | `*3\r\n$12\r\npunsubscribe\r\n$<len>\r\n<pattern>\r\n:<sub_count>\r\n` | None | `PUNSUBSCRIBE news.*` &rarr; `*3\r\n$12\r\npunsubscribe\r\n$6\r\nnews.*\r\n:0\r\n` |
| `PUBLISH` | `PUBLISH channel message`<br>Posts message to given channel, returning receiver count. | `:<count_of_clients_receiving_message>\r\n` | `!=2` args errors | `PUBLISH news "hello"` &rarr; `:1\r\n` |
| `PUBSUB` | `PUBSUB CHANNELS\|NUMSUB\|NUMPAT\|SHARDCHANNELS\|SHARDNUMSUB [args]` | Subcommand-specific inspection arrays/integers | Syntax errors | `PUBSUB CHANNELS` &rarr; `*1\r\n$4\r\nnews\r\n` |
| `SSUBSCRIBE` | `SSUBSCRIBE shardchannel [shardchannel ...]`<br>Subscribes to shard channel. | `*3\r\n$10\r\nssubscribe\r\n$<len>\r\n<chan>\r\n:<sub_count>\r\n` | `<1` arg errors | `SSUBSCRIBE orders` &rarr; `*3\r\n$10\r\nssubscribe\r\n$6\r\norders\r\n:1\r\n` |
| `SUNSUBSCRIBE` | `SUNSUBSCRIBE [shardchannel [shardchannel ...]]`<br>Unsubscribes from shard channel. | `*3\r\n$12\r\nsunsubscribe\r\n$<len>\r\n<chan>\r\n:<sub_count>\r\n` | None | `SUNSUBSCRIBE orders` &rarr; `*3\r\n$12\r\nsunsubscribe\r\n$6\r\norders\r\n:0\r\n` |
| `SPUBLISH` | `SPUBLISH shardchannel message`<br>Publishes message to shard channel. | `:<count_of_clients_receiving>\r\n` | `!=2` args errors | `SPUBLISH orders "new"` &rarr; `:1\r\n` |
