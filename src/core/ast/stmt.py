from __future__ import annotations

from dataclasses import dataclass, field
from abc import ABC

from src.core.ast.base import ASTNode, Identifier
import src.core.ast.base as _base
import src.core.ast.expr as _expr
from src.core.ast.expr import Expr

@dataclass
class Program():
    stmt: list[Stmt]

@dataclass(repr=False)
class Stmt(ASTNode, ABC):
    pass

@dataclass(repr=False)
class VariableStmt(Stmt, ABC):
    pass

@dataclass(repr=False)
class LetStmt(VariableStmt):
    left: Identifier
    right: Expr
    contract: _base.TypeNode

@dataclass(repr=False)
class RefStmt(VariableStmt):
    left: Identifier
    right: Expr
    contract: _base.TypeNode

@dataclass(repr=False)
class MoveStmt(VariableStmt):
    left: Identifier
    right: Expr
    contract: _base.TypeNode
