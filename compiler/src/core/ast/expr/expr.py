from abc import ABC
from dataclasses import dataclass

from src.core.ast import Node

@dataclass(frozen=True)
class Expr(Node, ABC):
    pass

