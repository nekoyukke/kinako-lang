from abc import ABC
from dataclasses import dataclass

from src.core.ast.expr import Expr
from src.core.ast.expr.binary.binary_kind import BinaryKind

@dataclass(frozen=True)
class BinaryExpr(Expr, ABC):
    kind: BinaryKind
    left: Expr
    right: Expr