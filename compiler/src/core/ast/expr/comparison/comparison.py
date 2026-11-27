
from dataclasses import dataclass

from src.core.ast.expr import Expr
from src.core.ast.expr.comparison.comparison_kind import ComparisonKind

@dataclass(frozen=True)
class ComparisonExpr(Expr):
    kind: ComparisonKind
    left: Expr
    right: Expr