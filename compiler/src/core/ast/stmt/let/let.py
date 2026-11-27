from src.core.ast.expr import Expr
from dataclasses import dataclass
from src.core.ast.stmt.stmt import Stmt
from src.core.ast.identifier import Identifier

@dataclass(frozen=True)
class LetStmt(Stmt):
    ty: 