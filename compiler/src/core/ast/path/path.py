
from dataclasses import dataclass
from src.core.ast.ast import Node
from src.core.ast.identifier import Identifier

@dataclass(frozen=True)
class Path(Node):
    segments: list[Identifier]