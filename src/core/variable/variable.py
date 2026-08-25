from dataclasses import dataclass

from src.core.source.source_span import SourceSpan
from src.core.contract.contract import Contract

@dataclass
class VariableDef:
    contract: Contract
    span: SourceSpan