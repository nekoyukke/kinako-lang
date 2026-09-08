from __future__ import annotations

from dataclasses import dataclass
from abc import ABC

from src.core.source.source_span import SourceSpan

@dataclass
class TypeDef(ABC):
    pass

# ビルドイン
@dataclass
class BuildinType(TypeDef, ABC):
    pass

@dataclass
class IntType(BuildinType):
    bit_size: int

@dataclass
class FloatType(BuildinType):
    bit_size: int

@dataclass
class BooleanType(BuildinType):
    pass

@dataclass
class NoneType(BuildinType):
    pass

@dataclass
class PtrType(BuildinType):
    element: TypeDef

@dataclass
class ArrayType(BuildinType):
    element: TypeDef
    size: int

@dataclass
class UnionType(BuildinType):
    right: TypeDef
    left: TypeDef

@dataclass
class LiteralType(TypeDef):
    pass

@dataclass
class NumberLiteral(LiteralType):
    pass

@dataclass
class FloatingLiteral(LiteralType):
    pass
@dataclass
class StringLiteral(LiteralType):
    pass

# 定義クラス
@dataclass
class UserDefType(TypeDef):
    member: list[TypeDef]
    span: SourceSpan