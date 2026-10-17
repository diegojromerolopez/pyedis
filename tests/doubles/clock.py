"""Deterministic clock test double."""


class MutableClock:
    """Callable clock whose value can be advanced by a test."""

    def __init__(self, value: float = 0.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds
