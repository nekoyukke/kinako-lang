from dataclasses import dataclass

from abc import ABC

@dataclass
class TypeDef(ABC):
    pass

@dataclass
class IntType(TypeDef):
    bit: int
    is_sign: bool # True -> 符号あり
    def __repr__(self) -> str:
        return f"{"i"*self.is_sign or"u"}{self.bit}"

@dataclass
class FloatType(TypeDef):
    bit: int
    def __repr__(self) -> str:
        return f"f{self.bit}"

@dataclass
class ArrayType(TypeDef):
    length: int
    def __repr__(self) -> str:
        return f"Array:{self.length}"

@dataclass
class PtrType(TypeDef):
    def __repr__(self) -> str:
        return "ptr"

@dataclass
class BoolType(TypeDef):
    def __repr__(self) -> str:
        return "bool"

@dataclass
class NoneType(TypeDef):
    def __repr__(self) -> str:
        return "none"

@dataclass
class FunctionType(TypeDef):
    """(T0, T1, ...) -> result_T => function[result_T, T0, T1, ...]"""
    def __repr__(self) -> str:
        return "Callee"

@dataclass
class UserDefType(TypeDef):
    name:str
    def __repr__(self) -> str:
        return self.name

@dataclass
class ImmediateType(TypeDef, ABC):
    pass

@dataclass
class IntegerImmediateType(ImmediateType):
    def __repr__(self) -> str:
        return "Immediate_Int"

@dataclass
class DecimalImmediateType(ImmediateType):
    def __repr__(self) -> str:
        return "Immediate_Float"

@dataclass
class StringImmediateType(ImmediateType):
    def __repr__(self) -> str:
        return "Immediate_Str"

@dataclass
class ContainerImmediateType(ImmediateType):
    def __repr__(self) -> str:
        return "Immediate_Container"
