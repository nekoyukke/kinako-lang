from dataclasses import dataclass

from src.core.span import Span


@dataclass(frozen=True)
class Symbol:
    span: Span
    name: str


@dataclass(frozen=True)
class RecordSymbol(Symbol):
    pass


@dataclass(frozen=True)
class FunctionSymbol(Symbol):
    pass


@dataclass(frozen=True)
class RQSymbol(Symbol):
    pass


@dataclass(frozen=True)
class DefSymbol(Symbol):
    pass


@dataclass(frozen=True)
class VarSymbol(Symbol):
    pass


@dataclass(frozen=True)
class LetSymbol(Symbol):
    pass


@dataclass(frozen=True)
class ParameterSymbol(Symbol):
    pass


@dataclass(frozen=True)
class ImplSymbol(Symbol):
    pass


@dataclass(frozen=True)
class InterfaceSymbol(Symbol):
    pass


@dataclass(frozen=True)
class StructSymbol(Symbol):
    pass


@dataclass(frozen=True)
class ClassSymbol(Symbol):
    pass


@dataclass(frozen=True)
class ModuleSymbol(Symbol):
    """`import foo.bar` によって導入される compile-time namespace。"""

    pass
