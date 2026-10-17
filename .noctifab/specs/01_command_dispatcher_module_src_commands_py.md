### 3.4 Command Dispatcher Module (`src/commands.py`)
```python
"""Command validation, execution routing, and RESP envelope generation."""
from src.store import Store
from src.persistence import AOFLogger

class CommandDispatcher:
    def __init__(self, store: Store, aof: AOFLogger | None = None) -> None:
        self.store: Store = store
        self.aof: AOFLogger | None = aof

    async def dispatch(self, args: list[bytes]) -> tuple[bytes, bool]:
        """
        Validates syntax/arity, routes command (case-insensitively), performs mutation,
        logs to AOF, and returns (resp_reply_bytes, should_close_connection).
        """
        ...
```
