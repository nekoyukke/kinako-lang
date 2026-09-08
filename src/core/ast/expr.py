from dataclasses import dataclass
from enum import Enum
from abc import ABC

from src.core.ast.base import ASTNode
from src.core.contract.type.type import TypeDef
from src.core.symbol.symbol import Symbol

@dataclass(repr=False)
class Expr(ASTNode, ABC):
    id: TypeDef | None

class BinaryKind(Enum):
    PLUS = "+"
    MINUS = "-"
    MULT = "*"
    DIV = "/"
    MOD = "%"
    LOGIC_OR = "||"
    LOGIC_AND = "&&"

@dataclass(repr=False)
class BinaryExpr(Expr):
    left: Expr
    right: Expr
    op: BinaryKind

class UnaryKind(Enum):
    PLUS = "+"
    MINUS = "-"

@dataclass(repr=False)
class UnaryExpr(Expr):
    expr: Expr
    op: UnaryKind

@dataclass(repr=False)
class Variable(Expr):
    ident: str
    symbol: Symbol | None = None

@dataclass(repr=False)
class CallExpr(Expr):
    call: Expr
    args: list[Expr]

class LogicKind(Enum):
    EQ = r'=='
    NE = r'!='
    LE = r'<='
    GE = r'>='
    GT = ">"
    LT = "<"

@dataclass(repr=False)
class LogicExpr(Expr):
    left: Expr
    right: Expr
    op: LogicKind

class AssignKind(Enum):
    ASSIGN = r'='
    PULS = r'+='
    MINUS = r'-='
    MULT = r'*='
    DIV = r'/='

@dataclass(repr=False)
class AssignExpr(Expr):
    left: Expr
    right: Expr
    op: AssignKind

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
    member: Variable


@dataclass(repr=False)
class Literal(Expr, ABC):
    pass

@dataclass(repr=False)
class BoolLiteral(Literal):
    is_true:bool

@dataclass(repr=False)
class IntLiteral(Literal):
    number:int

@dataclass(repr=False)
class FloatLiteral(Literal):
    number:float

@dataclass(repr=False)
class NoneLiteral(Literal):
    pass

@dataclass(repr=False)
class NullLiteral(Literal):
    pass

@dataclass(repr=False)
class StringLiteral(Literal):
    string:str


kinds = LogicKind | UnaryKind | AssignKind | BinaryKind
