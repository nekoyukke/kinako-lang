from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from abc import ABC

from src.core.ast.base import ASTNode, Identifier, Binding

@dataclass(repr=False)
class Expr(ASTNode, ABC):
    pass 

@dataclass(repr=False)
class Variable(Expr):
    name: Identifier

@dataclass(repr=False)
class BinaryExpr(Expr, ABC):
    pass

class ArithmeticKind(str, Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"

@dataclass(repr=False)
class ArithmeticExpr(BinaryExpr):
    kind: ArithmeticKind
    left: Expr
    right: Expr

class LogicKind(str, Enum):
    AND = "&&"
    OR = "||"

@dataclass(repr=False)
class LogicExpr(BinaryExpr):
    kind: LogicKind
    left: Expr
    right: Expr

class IdentityKind(str, Enum):
    EQ = "=="
    NE = "!="

@dataclass(repr=False)
class IdentityExpr(BinaryExpr):
    kind: IdentityKind
    left: Expr
    right: Expr

class CompKind(str, Enum):
    GT = ">"
    GE = ">="
    LT = "<"
    LE = "<="

@dataclass(repr=False)
class CompExpr(BinaryExpr):
    kind: CompKind
    left: Expr
    right: Expr

@dataclass(repr=False)
class AccessExpr(Expr, ABC):
    pass

@dataclass(repr=False)
class IndexExpr(AccessExpr):
    expr: Expr
    index: Expr

@dataclass(repr=False)
class MemberExpr(AccessExpr):
    expr: Expr
    name: Identifier

@dataclass(repr=False)
class UnaryExpr(Expr, ABC):
    pass

@dataclass(repr=False)
class Immediate(Expr, ABC):
    pass

@dataclass(repr=False)
class StringImmediate(Immediate):
    value:str

@dataclass(repr=False)
class IntegerImmediate(Immediate):
    value:int

@dataclass(repr=False)
class DecimalImmediate(Immediate):
    value:float

@dataclass(repr=False)
class ContainerImmediate(Immediate):
    value:list[Expr]

@dataclass(repr=False)
class DataExpr(Expr, ABC):
    pass

@dataclass(repr=False)
class MoveExpr(DataExpr):
    right: Expr
    left: Expr
    
@dataclass(repr=False)
class AssignExpr(DataExpr):
    right: Expr
    left: Expr
    
@dataclass(repr=False)
class RefExpr(DataExpr):
    right: Expr
    left: Expr
    split_right: Binding | None
