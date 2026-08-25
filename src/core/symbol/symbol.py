from __future__ import annotations

from dataclasses import dataclass
from abc import ABC
from typing import TYPE_CHECKING

from src.core.source.source_span import SourceSpan
from src.core.contract.contract import Contract

if TYPE_CHECKING:
    from src.core.ast.base import ASTNode

@dataclass(slots=True)
class Symbol(ABC):
    name: str
    span: SourceSpan

@dataclass(slots=True)
class VariableSymbol(Symbol):
    entity: Contract

@dataclass(slots=True)
class FunctionSymbol(Symbol):
    result: Contract
    parameters: list[VariableSymbol]
    declaration: ASTNode

@dataclass(slots=True)
class ClassSymbol(Symbol):
    members: dict[str, Symbol]

    def define_member(self, symbol: Symbol) -> None:
        self.members[symbol.name] = symbol

    def lookup_member(self, name: str) -> Symbol | None:
        return self.members.get(name)
