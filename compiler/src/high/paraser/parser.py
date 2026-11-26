from src.core.tokens import *
from src.core.ast import *

class Parser:
    def __init__(self) -> None:
        self.source: str
        self.tokens: list[Token]
        return