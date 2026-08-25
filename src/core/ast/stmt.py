from dataclasses import dataclass
from abc import ABC

from src.core.ast.base import ASTNode, Contract, Parameter
import src.core.ast.expr as _expr
from src.core.symbol.symbol import Symbol


@dataclass(repr=False)
class Stmt(ASTNode, ABC):
    pass

# 宣言系
@dataclass(repr=False)
class VariableDeclStmt(Stmt):
    name: _expr.Variable
    contract: Contract
    left: _expr.Expr | None
    symbol: Symbol | None = None

@dataclass(repr=False)
class FunctionDeclStmt(Stmt):
    name: _expr.Variable
    result: Contract
    params: list[Parameter]
    body: Stmt
    symbol: Symbol | None = None

# そのほか

@dataclass(repr=False)
class ExprStmt(Stmt):
    expr: _expr.Expr

@dataclass(repr=False)
class ReturnStmt(Stmt):
    expr: _expr.Expr

# ブロック系
@dataclass(repr=False)
class BlockStmt(Stmt):
    instr: list[Stmt]

@dataclass(repr=False)
class ProgramStmt(Stmt):
    instr: list[Stmt]

# 制御構文系
@dataclass(repr=False)
class Ifstmt(Stmt):
    cond: _expr.Expr
    then_stmt: Stmt
    else_stmt: Stmt | None

@dataclass(repr=False)
class WhileStmt(Stmt):
    cond: _expr.Expr
    loop: Stmt

@dataclass(repr=False)
class ForEachStmt(Stmt):
    iterator: _expr.Expr
    variable: _expr.Variable
    contract: Contract
    loop: Stmt
