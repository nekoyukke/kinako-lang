from typing import NamedTuple
from src.core.tokens.tokind import Tokenkind
from src.core.span import Span



class Token(NamedTuple):
    kind: Tokenkind
    span: Span