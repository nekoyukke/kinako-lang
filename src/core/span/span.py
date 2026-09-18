from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    """A location in source code."""

    line: int
    col: int
    len: int
