from __future__ import annotations
from dataclasses import dataclass

from src.core.symbol.symbol import Symbol

@dataclass(slots=True)
class Scope:
    parent: Scope | None
    symbols: dict[str, Symbol]

    def names(self) -> list[str]:
        """Return all visible names, honoring shadowing."""
        names = list(self.symbols)
        if self.parent is None:
            return names
        return names + [name for name in self.parent.names() if name not in self.symbols]

    def values(self) -> list[Symbol]:
        """Return all visible symbols, nearest definition first."""
        return [symbol for name in self.names() if (symbol := self.lookup(name)) is not None]

    def get_variable(self) -> list[str]:
        return self.names()
    
    def contains_local(self, name: str) -> bool:
        return name in self.symbols

    def check(self, name: str) -> bool:
        return self.lookup(name) is not None
    
    def lookup(self, name:str) -> Symbol|None:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def get_variable_db(self) -> list[Symbol]:
        return self.values()

    def define(self, symbol: Symbol) -> None:
        self.symbols[symbol.name] = symbol
