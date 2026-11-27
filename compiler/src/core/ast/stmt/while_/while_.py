from dataclasses import dataclass

from src.core.ast.expr import Expr
from src.core.ast.stmt.stmt import Stmt


@dataclass(frozen=True)
class WhileStmt(Stmt):
    condition: Expr
    body: tuple[Stmt, ...]
