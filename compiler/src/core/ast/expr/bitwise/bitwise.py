from abc import ABC
from dataclasses import dataclass

from src.core.ast.expr import Expr
from src.core.ast.expr.bitwise.bitwise_kind import BitwiseKind

@dataclass(frozen=True)
class BitwiseExpr(Expr, ABC):
    kind: BitwiseKind
    left: Expr
    right: Expr