from __future__ import annotations

from dataclasses import dataclass
from abc import ABC

from src.core.ast.base import ASTNode, Identifier
import src.core.ast.base as _base
from src.core.ast.expr import Expr


# =========================
# Program
# =========================

@dataclass(repr=False)
class Program(ASTNode):
    stmt: list[Stmt]


# =========================
# Common
# =========================

@dataclass(repr=False)
class Parameter(ASTNode):
    name: Identifier
    type: _base.TypeNode


# =========================
# Statement
# =========================

@dataclass(repr=False)
class Stmt(ASTNode, ABC):
    pass


@dataclass(repr=False)
class CompoundStmt(Stmt, ABC):
    pass


@dataclass(repr=False)
class SimpleStmt(Stmt, ABC):
    pass


@dataclass(repr=False)
class DeclStmt(Stmt, ABC):
    pass


# =========================
# Local declarations
# =========================

@dataclass(repr=False)
class LocalStmt(DeclStmt, ABC):
    pass


@dataclass(repr=False)
class LetStmt(LocalStmt):
    left: Identifier
    right: Expr
    contract: _base.TypeNode


@dataclass(repr=False)
class RefStmt(LocalStmt):
    left: Identifier
    right: Expr
    contract: _base.TypeNode


@dataclass(repr=False)
class MoveStmt(LocalStmt):
    left: Identifier
    right: Expr
    contract: _base.TypeNode


# =========================
# Variable declaration
# =========================

@dataclass(repr=False)
class VarDeclStmt(DeclStmt):
    name: Identifier
    type: _base.TypeNode | None = None
    value: Expr | None = None


# =========================
# Function
# =========================

@dataclass(repr=False)
class FunctionDeclStmt(DeclStmt, ABC):
    name: Identifier
    parms: list[Parameter]
    result: _base.TypeNode


@dataclass(repr=False)
class FunctionDefStmt(FunctionDeclStmt):
    body: Block


@dataclass(repr=False)
class FunctionPrototypeStmt(FunctionDeclStmt):
    pass

@dataclass(repr=False)
class FunctionStmt(FunctionDeclStmt):
    body: Block

# =========================
# CompoundStmt
# =========================

@dataclass(repr=False)
class Block(CompoundStmt):
    stmt: list[Stmt]


# =========================
# Record
# =========================

@dataclass(repr=False)
class RecordDeclStmt(DeclStmt):
    name: Identifier
    members: list[DeclStmt]


# =========================
# Interface
# =========================

@dataclass(repr=False)
class InterfaceDeclStmt(DeclStmt):
    name: Identifier
    members: list[FunctionPrototypeStmt]


# =========================
# Class
# =========================

@dataclass(repr=False)
class ClassDeclStmt(DeclStmt):
    name: Identifier
    members: list[ClassMemberStmt]


@dataclass(repr=False)
class ClassMemberStmt(ASTNode, ABC):
    pass


# struct use foo;
@dataclass(repr=False)
class StructUseStmt(ClassMemberStmt):
    name: Identifier


# struct { ... }
@dataclass(repr=False)
class StructDeclStmt(ClassMemberStmt):
    members: list[VarDeclStmt]


# impl use bar { ... }
@dataclass(repr=False)
class ImplUseStmt(ClassMemberStmt):
    interface: Identifier
    members: list[FunctionDefStmt]


# impl { ... }
@dataclass(repr=False)
class ImplStmt(ClassMemberStmt):
    members: list[FunctionDefStmt]