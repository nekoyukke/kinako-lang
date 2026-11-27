from enum import IntEnum, auto

class BitwiseKind(IntEnum):
    AND = auto()
    OR = auto()
    XOR = auto()
    SHL = auto()
    SHR = auto()