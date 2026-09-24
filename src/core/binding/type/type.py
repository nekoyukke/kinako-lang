from dataclasses import dataclass

from abc import ABC

@dataclass
class TypeDef(ABC):
    pass

@dataclass
class IntType(TypeDef):
    bit: int
    is_sign: bool # True -> 符号あり

@dataclass
class FloatType(TypeDef):
    bit: int

@dataclass
class ArrayType(TypeDef):
    length: int

@dataclass
class PtrType(TypeDef):
    pass

@dataclass
class BoolType(TypeDef):
    pass

@dataclass
class NoneType(TypeDef):
    pass

@dataclass
class FunctionType(TypeDef):
    """(T0, T1, ...) -> result_T => function[result_T, T0, T1, ...]"""

@dataclass
class UserDefType(TypeDef):
    name:str

@dataclass
class ImmediateType(TypeDef):
    pass

@dataclass
class IntegerImmediateType(ImmediateType):
    pass

@dataclass
class DecimalImmediateType(ImmediateType):
    pass

@dataclass
class StringImmediateType(ImmediateType):
    pass

@dataclass
class containerImmediateType(ImmediateType):
    pass
