# API reference

Commands follow Redis syntax. Missing values are encoded as null bulk strings and integer counters use RESP integer frames. Expirations are stored as absolute Unix timestamps, so replay does not renew a key's lifetime. The TCP server accepts both RESP arrays and CRLF-terminated inline commands.
