from dataclasses import dataclass

from src.core.symbol.symbol import FunctionSymbol, LetSymbol, ParameterSymbol


ScopedSymbol = LetSymbol | ParameterSymbol | FunctionSymbol

@dataclass
class Scope():
    parent: Scope | None
    symbol: dict[str, ScopedSymbol]

    def look_up(self, name: str) -> ScopedSymbol | None:
        if name in self.symbol:
            return self.symbol[name]
        if self.parent:
            return self.parent.look_up(name)
        return None
