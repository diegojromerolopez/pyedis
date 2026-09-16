from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Callable, Protocol


class Clock(Protocol):
    def __call__(self) -> float: ...


class Logger(Protocol):
    def __call__(self, message: str) -> None: ...


class Persistence:
    """Deterministic append-only persistence for key/value mutations.

    Records contain absolute expiration timestamps.  The file is opened only
    for the duration of an append, which makes write and fsync ordering easy
    to observe and prevents a leaked descriptor across server lifecycles.
    """

    def __init__(
        self,
        data_dir: str | os.PathLike[str],
        *,
        filename: str = "appendonly.aof",
        fsync: bool = True,
        clock: Clock | None = None,
        logger: Logger | None = None,
        opener: Callable[..., Any] | None = None,
        fsync_func: Callable[[int], None] | None = None,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.path = self.data_dir / filename
        self.fsync = fsync
        self.clock = clock or __import__("time").time
        self.logger = logger or (lambda _message: None)
        self._opener = opener or open
        self._fsync = fsync_func or os.fsync
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _encoded(value: bytes) -> str:
        return base64.b64encode(value).decode("ascii")

    @staticmethod
    def _decoded(value: str) -> bytes:
        return base64.b64decode(value.encode("ascii"), validate=True)

    def _record(self, operation: str, **fields: object) -> bytes:
        record = {"op": operation, **fields}
        return (
            json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"
        ).encode("utf-8")

    def _append(self, record: bytes) -> None:
        with self._opener(self.path, "ab") as stream:
            stream.write(record)
            stream.flush()
            if self.fsync:
                self._fsync(stream.fileno())

    def append_set(
        self, key: bytes, value: bytes, expire_at: float | None = None
    ) -> None:
        """Persist a SET mutation with an absolute expiration timestamp."""
        self._append(
            self._record(
                "set",
                key=self._encoded(key),
                value=self._encoded(value),
                expire_at=expire_at,
            )
        )

    def append_delete(self, keys: list[bytes] | tuple[bytes, ...]) -> None:
        """Persist deletion of one or more keys."""
        self._append(self._record("delete", keys=[self._encoded(key) for key in keys]))

    def append_flushall(self) -> None:
        """Persist and immediately apply a database flush mutation."""
        self._append(self._record("flushall"))

    # Convenient command-layer aliases.
    set = append_set
    delete = append_delete
    flushall = append_flushall

    def truncate(self) -> None:
        """Atomically reset the AOF to an empty file and honor fsync policy."""
        with self._opener(self.path, "wb") as stream:
            stream.flush()
            if self.fsync:
                self._fsync(stream.fileno())

    def replay(self, store: Any) -> None:
        """Replay records in file order into a supplied store.

        A malformed final, unterminated physical line is ignored.  Any other
        malformed line is an error because silently skipping it would lose a
        mutation from the middle of the history.
        """
        if not self.path.exists():
            return
        with self._opener(self.path, "rb") as stream:
            lines = stream.readlines()
        for index, raw_line in enumerate(lines):
            if not raw_line.strip():
                if index == len(lines) - 1 and not raw_line.endswith(b"\n"):
                    continue
                if index == len(lines) - 1:
                    continue
            try:
                record = json.loads(raw_line.decode("utf-8"))
                if not isinstance(record, dict):
                    raise ValueError("record is not an object")
                self._apply(record, store)
            except (
                ValueError,
                TypeError,
                KeyError,
                UnicodeError,
                json.JSONDecodeError,
                base64.binascii.Error,
            ) as exc:
                trailing = index == len(lines) - 1 and not raw_line.endswith(b"\n")
                if trailing:
                    self.logger("pyedis: ignoring corrupt trailing AOF line")
                    continue
                raise ValueError(
                    f"pyedis: corrupt AOF line {index + 1}: {exc}"
                ) from exc

    def _apply(self, record: dict[str, object], store: Any) -> None:
        operation = record.get("op")
        if operation == "set":
            key = self._decoded(self._required_string(record, "key"))
            value = self._decoded(self._required_string(record, "value"))
            expire_at = record.get("expire_at")
            if expire_at is not None and not isinstance(expire_at, (int, float)):
                raise ValueError("invalid expire_at")
            if expire_at is not None and float(expire_at) <= self.clock():
                self._delete(store, key)
                return
            try:
                store.set(key, value, expire_at=expire_at)
            except TypeError:
                store.set(key, value)
                if expire_at is not None and hasattr(store, "expires"):
                    store.expires[key] = float(expire_at)
        elif operation == "delete":
            keys = record.get("keys")
            if not isinstance(keys, list):
                raise ValueError("invalid keys")
            for encoded in keys:
                if not isinstance(encoded, str):
                    raise ValueError("invalid key")
                self._delete(store, self._decoded(encoded))
        elif operation == "flushall":
            if hasattr(store, "flushall"):
                store.flushall()
            elif hasattr(store, "clear"):
                store.clear()
            elif hasattr(store, "data"):
                store.data.clear()
                if hasattr(store, "expires"):
                    store.expires.clear()
        else:
            raise ValueError("unknown operation")

    @staticmethod
    def _required_string(record: dict[str, object], name: str) -> str:
        value = record.get(name)
        if not isinstance(value, str):
            raise ValueError(f"invalid {name}")
        return value

    @staticmethod
    def _delete(store: Any, key: bytes) -> None:
        try:
            store.delete([key])
        except TypeError:
            store.delete(key)


AOF = Persistence
