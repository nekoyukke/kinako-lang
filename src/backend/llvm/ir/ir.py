"""LLVM assembly を出力する直前の、最小限で型付きの IR。

この IR は一般的な middleend ではない。LLVM 固有の alloca/load/store や
terminator をそのまま持ち、後段の emitter が `.ll` テキストへ落とすための
データ構造である。識別子は `%` / `@` を付けない素の名前で保存する。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TypeAlias


# Types -----------------------------------------------------------------------


@dataclass(frozen=True)
class LLVMType:
    """LLVM 型の基底クラス。"""


@dataclass(frozen=True)
class VoidType(LLVMType):
    pass


@dataclass(frozen=True)
class IntegerType(LLVMType):
    bits: int

    def __post_init__(self) -> None:
        if self.bits <= 0:
            raise ValueError("integer bit width must be positive")


@dataclass(frozen=True)
class FloatType(LLVMType):
    """LLVM の浮動小数点型名。最初は `float` と `double` を使う。"""

    name: str

    def __post_init__(self) -> None:
        if self.name not in {"half", "float", "double"}:
            raise ValueError(f"unsupported LLVM floating-point type: {self.name}")


@dataclass(frozen=True)
class PointerType(LLVMType):
    """Opaque pointer。pointee は emitter 用の意味情報で、出力は通常 `ptr`。"""

    pointee: LLVMType | None = None


@dataclass(frozen=True)
class ArrayType(LLVMType):
    length: int
    element: LLVMType

    def __post_init__(self) -> None:
        if self.length < 0:
            raise ValueError("array length cannot be negative")


@dataclass(frozen=True)
class NamedStructType(LLVMType):
    """`%Name` として参照する named struct 型。"""

    name: str


@dataclass(frozen=True)
class FunctionType(LLVMType):
    result: LLVMType
    parameters: tuple[LLVMType, ...]
    is_vararg: bool = False


@dataclass(frozen=True)
class StructDeclaration:
    """`%name = type { ... }`。fields=None は opaque struct を表す。"""

    name: str
    fields: tuple[LLVMType, ...] | None


# Values ----------------------------------------------------------------------


@dataclass(frozen=True)
class LocalValue:
    """`%name` で参照する SSA 値または stack slot。"""

    name: str
    type: LLVMType


@dataclass(frozen=True)
class GlobalValue:
    """`@name` で参照する関数・グローバル値。"""

    name: str
    type: LLVMType


@dataclass(frozen=True)
class IntegerConstant:
    type: IntegerType
    value: int


@dataclass(frozen=True)
class FloatConstant:
    type: FloatType
    value: float


@dataclass(frozen=True)
class NullConstant:
    type: PointerType


@dataclass(frozen=True)
class UndefValue:
    type: LLVMType


Value: TypeAlias = (
    LocalValue
    | GlobalValue
    | IntegerConstant
    | FloatConstant
    | NullConstant
    | UndefValue
)


@dataclass(frozen=True)
class Parameter:
    value: LocalValue


# Instructions ----------------------------------------------------------------


@dataclass(frozen=True)
class Instruction:
    """Terminator 以外の LLVM 命令の基底クラス。"""


@dataclass(frozen=True)
class Alloca(Instruction):
    result: LocalValue
    allocated_type: LLVMType


@dataclass(frozen=True)
class Load(Instruction):
    result: LocalValue
    address: Value


@dataclass(frozen=True)
class Store(Instruction):
    value: Value
    address: Value


class BinaryOp(str, Enum):
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    SDIV = "sdiv"
    SREM = "srem"
    FADD = "fadd"
    FSUB = "fsub"
    FMUL = "fmul"
    FDIV = "fdiv"
    AND = "and"
    OR = "or"


@dataclass(frozen=True)
class Binary(Instruction):
    result: LocalValue
    op: BinaryOp
    left: Value
    right: Value


class CompareOp(str, Enum):
    EQ = "eq"
    NE = "ne"
    SGT = "sgt"
    SGE = "sge"
    SLT = "slt"
    SLE = "sle"
    OEQ = "oeq"
    ONE = "one"
    OGT = "ogt"
    OGE = "oge"
    OLT = "olt"
    OLE = "ole"


@dataclass(frozen=True)
class Compare(Instruction):
    """整数比較は icmp、浮動小数点比較は fcmp として emitter が選択する。"""

    result: LocalValue
    op: CompareOp
    left: Value
    right: Value


class CastOp(str, Enum):
    SEXT = "sext"
    TRUNC = "trunc"
    SITOFP = "sitofp"
    FPTOSI = "fptosi"
    BITCAST = "bitcast"


@dataclass(frozen=True)
class Cast(Instruction):
    result: LocalValue
    op: CastOp
    value: Value


@dataclass(frozen=True)
class Call(Instruction):
    callee: GlobalValue
    arguments: tuple[Value, ...]
    result: LocalValue | None = None


@dataclass(frozen=True)
class InlineAsm(Instruction):
    template: str
    constraints: str = ""
    side_effect: bool = True


@dataclass(frozen=True)
class GetElementPtr(Instruction):
    result: LocalValue
    element_type: LLVMType
    address: Value
    indices: tuple[Value, ...]


# Control flow ----------------------------------------------------------------


@dataclass(frozen=True)
class Terminator:
    """各 basic block の末尾に必ず一つ置く制御フロー命令。"""


@dataclass(frozen=True)
class Return(Terminator):
    value: Value | None = None


@dataclass(frozen=True)
class Branch(Terminator):
    target: str


@dataclass(frozen=True)
class ConditionalBranch(Terminator):
    condition: Value
    then_target: str
    else_target: str


@dataclass(frozen=True)
class Unreachable(Terminator):
    pass


@dataclass
class BasicBlock:
    label: str
    instructions: list[Instruction] = field(default_factory=list)
    terminator: Terminator | None = None

    def terminate(self, terminator: Terminator) -> None:
        """終端命令を一度だけ設定する。"""
        if self.terminator is not None:
            raise ValueError(f"basic block '{self.label}' already has a terminator")
        self.terminator = terminator

    def append(self, instruction: Instruction) -> None:
        """終端済み block に通常命令を追加するのを防ぐ。"""
        if self.terminator is not None:
            raise ValueError(f"cannot append to terminated basic block '{self.label}'")
        self.instructions.append(instruction)


# Module ----------------------------------------------------------------------


@dataclass(frozen=True)
class ExternalFunction:
    name: str
    type: FunctionType


@dataclass(frozen=True)
class GlobalVariable:
    name: str
    type: LLVMType
    initializer: Value


@dataclass
class Function:
    name: str
    type: FunctionType
    parameters: tuple[Parameter, ...]
    blocks: list[BasicBlock] = field(default_factory=list)

    def append_block(self, block: BasicBlock) -> None:
        if any(current.label == block.label for current in self.blocks):
            raise ValueError(f"duplicate basic block label: {block.label}")
        self.blocks.append(block)


@dataclass
class Module:
    name: str
    type_declarations: list[StructDeclaration] = field(default_factory=list)
    external_functions: list[ExternalFunction] = field(default_factory=list)
    globals: list[GlobalVariable] = field(default_factory=list)
    functions: list[Function] = field(default_factory=list)

    def append_function(self, function: Function) -> None:
        if any(current.name == function.name for current in self.functions):
            raise ValueError(f"duplicate function name: {function.name}")
        self.functions.append(function)
