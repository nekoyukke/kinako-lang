from __future__ import annotations
from typing import NamedTuple



class Span(NamedTuple):
    len: int
    start: int
    end: int