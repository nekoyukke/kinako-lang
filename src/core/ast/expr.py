from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from abc import ABC

from src.core.ast.base import ASTNode, Identifier
import src.core.ast.base as _base
from src.core.binding.binding import Binding as SemanticBinding

@dataclass(repr=False, eq=False)
class Expr(ASTNode, ABC):
    pass 

@dataclass(repr=False, eq=False)
class Variable(Expr):
    name: Identifier

@dataclass(repr=False, eq=False)
class BinaryExpr(Expr, ABC):
    pass

class ArithmeticKind(str, Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"

@dataclass(repr=False, eq=False)
class ArithmeticExpr(BinaryExpr):
    kind: ArithmeticKind
    left: Expr
    right: Expr

class LogicKind(str, Enum):
    AND = "&&"
    OR = "||"

@dataclass(repr=False, eq=False)
class LogicExpr(BinaryExpr):
    kind: LogicKind
    left: Expr
    right: Expr

class IdentityKind(str, Enum):
    EQ = "=="
    NE = "!="

@dataclass(repr=False, eq=False)
class IdentityExpr(BinaryExpr):
    kind: IdentityKind
    left: Expr
    right: Expr

class CompKind(str, Enum):
    GT = ">"
    GE = ">="
    LT = "<"
    LE = "<="

@dataclass(repr=False, eq=False)
class CompExpr(BinaryExpr):
    kind: CompKind
    left: Expr
    right: Expr

@dataclass(repr=False, eq=False)
class AccessExpr(Expr, ABC):
    pass

@dataclass(repr=False, eq=False)
class IndexExpr(AccessExpr):
    expr: Expr
    index: Expr

@dataclass(repr=False, eq=False)
class MemberExpr(AccessExpr):
    expr: Expr
    name: Identifier

@dataclass(repr=False, eq=False)
class CallExpr(AccessExpr):
    """callee(args...)。callee 自身も MemberExpr などの後置式になれる。"""
    callee: Expr
    args: list[Expr]


@dataclass(repr=False, eq=False)
class CastExpr(AccessExpr):
    """`value as Type`。変換可否は checker が判断する。"""

    expr: Expr
    target: _base.TypeNode

@dataclass(repr=False, eq=False)
class UnaryExpr(Expr, ABC):
    pass

@dataclass(repr=False, eq=False)
class Immediate(Expr, ABC):
    pass

@dataclass(repr=False, eq=False)
class StringImmediate(Immediate):
    value:str

@dataclass(repr=False, eq=False)
class IntegerImmediate(Immediate):
    value:int

@dataclass(repr=False, eq=False)
class DecimalImmediate(Immediate):
    value:float

@dataclass(repr=False, eq=False)
class ContainerImmediate(Immediate):
    value:list[Expr]

@dataclass(repr=False, eq=False)
class NoneImmediate(Immediate):
    pass

@dataclass(repr=False, eq=False)
class NullImmediate(Immediate):
    pass

@dataclass(repr=False, eq=False)
class DataExpr(Expr, ABC):
    pass

@dataclass(repr=False, eq=False)
class MoveExpr(DataExpr):
    right: Expr
    left: Expr
    
@dataclass(repr=False, eq=False)
class AssignExpr(DataExpr):
    right: Expr
    left: Expr
    
@dataclass(repr=False, eq=False)
class RefExpr(DataExpr):
    right: Expr
    left: Expr
    split_right: SemanticBinding | None
