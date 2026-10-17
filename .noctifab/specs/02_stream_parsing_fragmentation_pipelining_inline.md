### 5.2 Stream Parsing, Fragmentation, Pipelining & Inline Commands
1. **TCP Stream Buffering & Chunking:** TCP provides a continuous stream with no packet boundary guarantees. The RESP decoder must accumulate incoming chunks in a stream buffer and yield parsed commands only when complete payloads (matching byte lengths and terminating `\r\n`) are received. Incomplete frames must remain buffered without blocking or crashing.
2. **Command Pipelining:** Clients may send multiple concatenated RESP commands in a single TCP read buffer. The server must process all commands sequentially in FIFO order and return all RESP replies in matching order without dropping or interleaving frames.
3. **Multi-Bulk Arrays vs. Inline Commands:**
   - Standard client libraries (`redis-py`, `redis-cli`) send commands formatted as RESP Multi-Bulk Arrays (e.g. `*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n`).
   - Telnet, netcat, and health checkers send plain text **Inline Commands** separated by whitespace and terminated by `\r\n` (e.g. `PING\r\n`, `PING hello\r\n`, `SET k v\r\n`). The decoder must support both formats seamlessly.
4. **Binary Safety:** Bulk strings must handle arbitrary byte sequences, including UTF-8 multi-byte characters, embedded `\r\n`, whitespace, and null bytes (`\x00`).
5. **Command Case-Insensitivity:** Command names are case-insensitive (`ping`, `PING`, `Ping`, `sEt`, `gEt` must all route to the same handler). Arguments/keys retain their exact case.

---
