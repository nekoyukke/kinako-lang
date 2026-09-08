from dataclasses import dataclass, field

from src.core.contract.type.type import TypeDef
from src.core.contract.right.right import Right
from src.core.contract.policy.policy import Policy
from src.core.symbol.symbol import Symbol


@dataclass(frozen=True, slots=True)
class ExprInfo:
    """The semantic result of checking one expression.

    A missing value means that its rule has not been implemented yet or that
    an earlier check could not determine it.
    """

    type: TypeDef
    right: Right
    policy: Policy | None = None

@dataclass(slots=True)
class Context:
    """Global semantic state.

    Only top-level declarations belong here. Members and methods belong to
    their ClassSymbol and are deliberately not flattened into this namespace.
    """

    symbols: dict[str, Symbol] = field(default_factory=dict[str, Symbol])
    types: list[TypeDef] = field(default_factory=list[TypeDef])
    right: dict[str, Right] = field(default_factory=dict[str, Right])
    policy: dict[str, Policy] = field(default_factory=dict[str, Policy])
    buildin_type: dict[str, TypeDef] = field(default_factory=dict[str, TypeDef])

    variable_type: dict[Symbol, TypeDef] = field(default_factory=dict[Symbol, TypeDef])

    def define(self, symbol: Symbol) -> None:
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Symbol | None:
        return self.symbols.get(name)

    def intern_type(self, type_def: TypeDef) -> TypeDef:
        for existing in self.types:
            if existing == type_def:
                return existing
        self.types.append(type_def)
        return type_def
