from dataclasses import dataclass
from abc import ABC

from src.core.ast.ast import Node

@dataclass(frozen=True)
class TypeExpr(Node, ABC):
    pass

@dataclass
class 