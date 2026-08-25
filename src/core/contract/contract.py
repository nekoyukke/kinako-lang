from dataclasses import dataclass

from src.core.contract.type.type import TypeDef
from src.core.contract.right.right import Right
from src.core.contract.policy.policy import Policy

@dataclass
class Contract:
    type: TypeDef | None
    right: Right | None
    policy: Policy | None
