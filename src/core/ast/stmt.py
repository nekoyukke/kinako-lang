from __future__ import annotations

from dataclasses import dataclass
from abc import ABC

from src.core.ast.base import ASTNode, Identifier
import src.core.ast.base as _base
from src.core.ast.expr import Expr


# =========================
# Program
# =========================

@dataclass(repr=False, eq=False)
class Program(ASTNode):
    stmt: list[Stmt]


# =========================
# Common
# =========================

@dataclass(repr=False, eq=False)
class Parameter(ASTNode):
    name: Identifier
    type: _base.TypeNode


# =========================
# Statement
# =========================

@dataclass(repr=False, eq=False)
class Stmt(ASTNode, ABC):
    pass


@dataclass(repr=False, eq=False)
class CompoundStmt(Stmt, ABC):
    pass


@dataclass(repr=False, eq=False)
class SimpleStmt(Stmt, ABC):
    pass


@dataclass(repr=False, eq=False)
class UnsafeStmt(SimpleStmt):
    """`unsafe <SimpleStmt>`。checker が中身を検査せず通すための境界。"""

    inner: SimpleStmt


@dataclass(repr=False, eq=False)
class DeclStmt(SimpleStmt, ABC):
    pass

# =========================
# Expr Stmt
# =========================

@dataclass(repr=False, eq=False)
class ExprStmt(SimpleStmt, ABC):
    expr: Expr

# =========================
# Local declarations
# =========================

@dataclass(repr=False, eq=False)
class LocalStmt(DeclStmt, ABC):
    pass


@dataclass(repr=False, eq=False)
class LetStmt(LocalStmt):
    left: Identifier
    right: Expr | None
    contract: _base.TypeNode | None


@dataclass(repr=False, eq=False)
class RefStmt(LocalStmt):
    left: Identifier
    right: Expr | None
    contract: _base.TypeNode | None


@dataclass(repr=False, eq=False)
class MoveStmt(LocalStmt):
    left: Identifier
    right: Expr | None
    contract: _base.TypeNode | None


# =========================
# Variable declaration
# =========================

@dataclass(repr=False, eq=False)
class VarDeclStmt(DeclStmt):
    name: Identifier
    type: _base.TypeNode | None = None


# =========================
# Function
# =========================

@dataclass(repr=False, eq=False)
class FunctionDeclStmt(DeclStmt, ABC):
    name: Identifier
    parms: list[Parameter]
    result: _base.TypeNode


@dataclass(repr=False, eq=False)
class FunctionDefStmt(FunctionDeclStmt):
    body: Block


@dataclass(repr=False, eq=False)
class FunctionRequestStmt(FunctionDeclStmt):
    pass

@dataclass(repr=False, eq=False)
class FunctionStmt(FunctionDeclStmt):
    body: Block

# =========================
# CompoundStmt
# =========================

@dataclass(repr=False, eq=False)
class Block(CompoundStmt):
    stmt: list[Stmt]

@dataclass(repr=False, eq=False)
class IfStmt(CompoundStmt):
    then_block: Stmt
    else_block: Stmt | None
    cond: Expr

@dataclass(repr=False, eq=False)
class WhileStmt(CompoundStmt):
    block: Stmt
    cond: Expr

# =========================
# Record
# =========================

@dataclass(repr=False, eq=False)
class RecordDeclStmt(DeclStmt):
    name: Identifier
    members: list[DeclStmt]


# =========================
# Interface
# =========================

@dataclass(repr=False, eq=False)
class InterfaceDeclStmt(DeclStmt):
    name: Identifier
    members: list[FunctionRequestStmt]


# =========================
# Class
# =========================

@dataclass(repr=False, eq=False)
class ClassDeclStmt(DeclStmt):
    name: Identifier
    members: list[ClassMemberStmt]


@dataclass(repr=False, eq=False)
class ClassMemberStmt(ASTNode, ABC):
    pass


# struct use foo;
@dataclass(repr=False, eq=False)
class StructUseStmt(ClassMemberStmt):
    name: Identifier


# struct { ... }
@dataclass(repr=False, eq=False)
class StructDeclStmt(ClassMemberStmt):
    members: list[VarDeclStmt]


# impl use bar { ... }
@dataclass(repr=False, eq=False)
class ImplUseStmt(ClassMemberStmt):
    interface: Identifier
    members: list[FunctionDefStmt]


# impl { ... }
@dataclass(repr=False, eq=False)
class ImplStmt(ClassMemberStmt):
    members: list[FunctionDefStmt]

@dataclass(repr=False, eq=False)
class ReturnStmt(SimpleStmt):
    value: Expr
