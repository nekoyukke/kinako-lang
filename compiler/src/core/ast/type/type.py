from dataclasses import dataclass
from abc import ABC

from src.core.ast.ast import Node
from src.core.ast.path import Path
from src.core.ast.expr import Expr

@dataclass(frozen=True)
class TypeExpr(Node, ABC):
    pass


@dataclass(frozen=True)
class PathTypeExpr(TypeExpr):
    path: Path
    type_args: tuple[TypeExpr, ...] = ()

@dataclass(frozen=True)
class ArrayTypeExpr(TypeExpr):
    inner: TypeExpr
    size: Expr


@dataclass(frozen=True)
class SliceTypeExpr(TypeExpr):
    inner: TypeExpr


@dataclass(frozen=True)
class PtrTypeExpr(TypeExpr):
    policy: Path
    access: Path | None
    inner: TypeExpr


@dataclass(frozen=True)
class RefTypeExpr(TypeExpr):
    rights: Right
    inner: TypeExpr