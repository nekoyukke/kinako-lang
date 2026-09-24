from dataclasses import dataclass
from pprint import pformat
from typing import ClassVar

from src.core.symbol import *
from src.core.binding.binding import *
from src.core.ast.base import ASTNode
from src.core.ast.expr import Expr


def _format_context(name: str, fields: list[tuple[str, object]]) -> str:
    lines = [f"{name}("]
    for field_name, value in fields:
        rendered = pformat(value, width=100, sort_dicts=False)
        lines.append(f"  {field_name}={rendered.replace(chr(10), chr(10) + '  ')},")
    lines.append(")")
    return "\n".join(lines)

@dataclass
class DeclarationContext:
    var: ClassVar[dict[VarSymbol, Binding]] = {}
    let: ClassVar[dict[LetSymbol, Binding]] = {}
    parameter: ClassVar[dict[ParameterSymbol, Binding]] = {}

    function: ClassVar[dict[FunctionSymbol, Binding]] = {}
    rq: ClassVar[dict[RQSymbol, Binding]] = {}
    define: ClassVar[dict[DefSymbol, Binding]] = {}

    def __repr__(self) -> str:
        return _format_context(
            "DeclarationContext",
            [
                ("var", self.var),
                ("let", self.let),
                ("parameter", self.parameter),
                ("function", self.function),
                ("rq", self.rq),
                ("define", self.define),
            ],
        )

@dataclass
class GeneralContext:

    default_policy: Policy
    default_right: Right

    sym: ClassVar[dict[ASTNode, Symbol]] = {}
    # Symbol が宣言された字句スコープの深さ。root は 0、内側ほど大きい。
    scope_depth: ClassVar[dict[Symbol, int]] = {}
    binding: dict[Expr, Binding]

    types: ClassVar[dict[str, TypeDef]] = {}
    rights: ClassVar[dict[str, Right]] = {}
    policies: ClassVar[dict[str, Policy]] = {}

    # Top-level declarations
    classes: ClassVar[dict[str, ClassSymbol]] = {}
    records: ClassVar[dict[str, RecordSymbol]] = {}
    interfaces: ClassVar[dict[str, InterfaceSymbol]] = {}
    top_function: ClassVar[dict[str, FunctionSymbol]] = {}

    # Class members and relationships
    struct_cls: ClassVar[dict[ClassSymbol, list[StructSymbol]]] = {}
    structs_by_name: ClassVar[dict[ClassSymbol, dict[str, StructSymbol]]] = {}
    member_struct: ClassVar[dict[StructSymbol, list[VarSymbol]]] = {}
    struct_vars_by_name: ClassVar[dict[StructSymbol, dict[str, VarSymbol]]] = {}
    record_struct: ClassVar[dict[StructSymbol, RecordSymbol]] = {}

    impl_cls: ClassVar[dict[ClassSymbol, list[ImplSymbol]]] = {}
    impls_by_name: ClassVar[dict[ClassSymbol, dict[str, ImplSymbol]]] = {}
    interface_impl: ClassVar[dict[ImplSymbol, InterfaceSymbol]] = {}
    define_impl: ClassVar[dict[ImplSymbol, list[DefSymbol]]] = {}

    # Record members
    member_record: ClassVar[dict[RecordSymbol, list[VarSymbol]]] = {}
    record_vars_by_name: ClassVar[dict[RecordSymbol, dict[str, VarSymbol]]] = {}

    # Interface members
    rq_interface: ClassVar[dict[InterfaceSymbol, list[RQSymbol]]] = {}
    rqs_by_name: ClassVar[dict[InterfaceSymbol, dict[str, RQSymbol]]] = {}

    # Impl members
    defs_by_name: ClassVar[dict[ImplSymbol, dict[str, DefSymbol]]] = {}
    # Record の field 表と同じく、Class ごとに def を名前から引けるようにする。
    class_defs_by_name: ClassVar[dict[ClassSymbol, dict[str, DefSymbol]]] = {}

    @staticmethod
    def _node_label(node: ASTNode) -> str:
        return f"{type(node).__name__}@{node.line}:{node.col}"

    def _symbol_entries(self) -> dict[str, Symbol]:
        return {
            self._node_label(node): symbol
            for node, symbol in self.sym.items()
        }

    def _binding_entries(self) -> dict[str, Binding]:
        return {
            self._node_label(node): binding
            for node, binding in self.binding.items()
        }

    def __repr__(self) -> str:
        return _format_context(
            "GeneralContext",
            [
                ("default_policy", self.default_policy),
                ("default_right", self.default_right),
                ("sym", self._symbol_entries()),
                ("scope_depth", self.scope_depth),
                ("binding", self._binding_entries()),
                ("types", self.types),
                ("rights", self.rights),
                ("policies", self.policies),
                ("classes", self.classes),
                ("records", self.records),
                ("interfaces", self.interfaces),
                ("top_function", self.top_function),
                ("struct_cls", self.struct_cls),
                ("structs_by_name", self.structs_by_name),
                ("member_struct", self.member_struct),
                ("struct_vars_by_name", self.struct_vars_by_name),
                ("record_struct", self.record_struct),
                ("impl_cls", self.impl_cls),
                ("impls_by_name", self.impls_by_name),
                ("interface_impl", self.interface_impl),
                ("define_impl", self.define_impl),
                ("member_record", self.member_record),
                ("record_vars_by_name", self.record_vars_by_name),
                ("rq_interface", self.rq_interface),
                ("rqs_by_name", self.rqs_by_name),
                ("defs_by_name", self.defs_by_name),
                ("class_defs_by_name", self.class_defs_by_name),
            ],
        )

@dataclass
class context:
    contract: DeclarationContext
    general: GeneralContext

    def __repr__(self) -> str:
        return _format_context(
            "context",
            [("contract", self.contract), ("general", self.general)],
        )
