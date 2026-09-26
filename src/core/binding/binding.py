from dataclasses import dataclass

from abc import ABC

from src.core.binding.type.type import *
from src.core.binding.right.right import *
from src.core.binding.policy.policy import *

@dataclass
class Binding(ABC):
    pass

@dataclass
class AtomicBinding(Binding):
    type: TypeDef
    right: Right
    policy: Policy
    is_ref: bool
    def __repr__(self) -> str:
        return f"{"ref "*self.is_ref}{self.type}{"@"+self.right.__repr__()}{"@"+self.policy.__repr__()}"

@dataclass
class AppliedBinding(Binding):
    atomic: AtomicBinding
    args: list[Binding]
    def __repr__(self) -> str:
        return f"{self.atomic}[{", ".join([i.__repr__() for i in self.args])}]"