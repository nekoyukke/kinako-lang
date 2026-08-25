from dataclasses import dataclass

from src.core.ast.base import ASTNode
from src.core.symbol.symbol import FunctionSymbol

@dataclass
class FunctionDef:
    symbol: FunctionSymbol
    body: ASTNode
