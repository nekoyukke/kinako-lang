from abc import ABC
from dataclasses import dataclass

from src.core.ast.expr import Expr

@dataclass(frozen=True)
class MovExpr(Expr, ABC):
    expr: Expr