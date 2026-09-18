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

@dataclass
class AppliedBinding(Binding):
    atomic: AtomicBinding
    args: list[Binding]
