"""Collect declarations, symbols, bindings, and relationships from a Kinako AST."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, TypeVar

from src.core.ast import base as _base
from src.core.ast import stmt as _stmt
from src.core.ast.base import ASTNode
from src.core.binding.binding import AppliedBinding, AtomicBinding, Binding
from src.core.binding.policy.policy import Policy
from src.core.binding.right.right import AccessKind, IdentityKind, Right
from src.core.binding.type.type import UserDefType
from src.core.context.context import DeclarationContext, GeneralContext, context
from src.core.span import Span
from src.core.symbol import (
    ClassSymbol,
    DefSymbol,
    FunctionSymbol,
    ImplSymbol,
    InterfaceSymbol,
    LetSymbol,
    ParameterSymbol,
    RQSymbol,
    RecordSymbol,
    StructSymbol,
    Symbol,
    VarSymbol,
)
from src.utils.error.collector import KinakoCollectorError
from src.utils.error.code import ErrorCode


SymbolT = TypeVar("SymbolT", bound=Symbol)


@dataclass(frozen=True)
class CollectionResult:
    context: context


class Collector:
    """First frontend pass: collect declarations without resolving references."""

    _REGISTRIES: ClassVar[tuple[type[DeclarationContext] | type[GeneralContext], ...]] = (
        DeclarationContext,
        GeneralContext,
    )

    def __init__(
        self, collected_context: context | None = None, source: str = ""
    ) -> None:
        if collected_context is None:
            collected_context = context(
                DeclarationContext(),
                GeneralContext(
                    default_policy=Policy(),
                    default_right=Right(AccessKind.NON, IdentityKind.SHARED),
                    binding={},
                ),
            )
        self.context = collected_context
        self.source = source
        self._pending_bindings: list[tuple[Symbol, _base.TypeNode, ASTNode]] = []

    @classmethod
    def clear(cls) -> None:
        """Clear the explicit shared Context registries before a fresh run."""
        for registry in cls._REGISTRIES:
            for value in vars(registry).values():
                if isinstance(value, dict):
                    value.clear()

    def collect(self, program: _stmt.Program) -> CollectionResult:
        self._pending_bindings.clear()
        for statement in program.stmt:
            self._collect_statement(statement, top_level=True)
        self._bind()
        return CollectionResult(self.context)

    def _collect_statement(
        self,
        statement: _stmt.Stmt,
        *,
        top_level: bool = False,
    ) -> None:
        match statement:
            case _stmt.LetStmt() | _stmt.RefStmt() | _stmt.MoveStmt():
                self._collect_let(statement)
            case _stmt.FunctionStmt():
                self._collect_function(statement, top_level=top_level)
            case _stmt.RecordDeclStmt():
                self._collect_record(statement)
            case _stmt.InterfaceDeclStmt():
                self._collect_interface(statement)
            case _stmt.ClassDeclStmt():
                self._collect_class(statement)
            case _stmt.Block():
                self._collect_block(statement)
            case _stmt.IfStmt():
                self._collect_statement(statement.then_block)
                if statement.else_block is not None:
                    self._collect_statement(statement.else_block)
            case _stmt.WhileStmt():
                self._collect_statement(statement.block)
            case _:
                # Expressions, returns, and assignments introduce no names.
                return

    def _collect_block(self, block: _stmt.Block) -> None:
        for statement in block.stmt:
            self._collect_statement(statement)

    def _collect_let(
        self,
        statement: _stmt.LetStmt | _stmt.RefStmt | _stmt.MoveStmt,
    ) -> None:
        symbol = LetSymbol(self._span(statement), statement.left.name)
        self.context.general.sym[statement] = symbol
        if statement.contract is not None:
            self._schedule_binding(symbol, statement.contract, statement)

    def _collect_function(
        self,
        statement: _stmt.FunctionStmt,
        *,
        top_level: bool,
    ) -> None:
        symbol = FunctionSymbol(self._span(statement), statement.name.name)
        self.context.general.sym[statement] = symbol
        if top_level:
            self._declare_global(
                self.context.general.top_function,
                symbol,
                statement,
            )

        for parameter in statement.parms:
            parameter_symbol = ParameterSymbol(self._span(parameter), parameter.name.name)
            self.context.general.sym[parameter] = parameter_symbol
            self._schedule_binding(parameter_symbol, parameter.type, parameter)
        self._collect_block(statement.body)

    def _collect_record(self, record: _stmt.RecordDeclStmt) -> None:
        symbol = RecordSymbol(self._span(record), record.name.name)
        self._declare_global(self.context.general.records, symbol, record)
        self._declare_type(symbol.name, record)
        self.context.general.sym[record] = symbol

        members: list[VarSymbol] = []
        by_name: dict[str, VarSymbol] = {}
        for member in record.members:
            if not isinstance(member, _stmt.VarDeclStmt):
                continue
            field = VarSymbol(self._span(member), member.name.name)
            self._declare_member(by_name, field, member)
            self.context.general.sym[member] = field
            if member.type is not None:
                self._schedule_binding(field, member.type, member)
            members.append(field)
        self.context.general.member_record[symbol] = members
        self.context.general.record_vars_by_name[symbol] = by_name

    def _collect_interface(self, interface: _stmt.InterfaceDeclStmt) -> None:
        symbol = InterfaceSymbol(self._span(interface), interface.name.name)
        self._declare_global(self.context.general.interfaces, symbol, interface)
        self._declare_type(symbol.name, interface)
        self.context.general.sym[interface] = symbol

        requests: list[RQSymbol] = []
        by_name: dict[str, RQSymbol] = {}
        for request in interface.members:
            request_symbol = RQSymbol(self._span(request), request.name.name)
            self._declare_member(by_name, request_symbol, request)
            self.context.general.sym[request] = request_symbol
            for parameter in request.parms:
                parameter_symbol = ParameterSymbol(
                    self._span(parameter), parameter.name.name
                )
                self.context.general.sym[parameter] = parameter_symbol
                self._schedule_binding(parameter_symbol, parameter.type, parameter)
            requests.append(request_symbol)
        self.context.general.rq_interface[symbol] = requests
        self.context.general.rqs_by_name[symbol] = by_name

    def _collect_class(self, class_: _stmt.ClassDeclStmt) -> None:
        symbol = ClassSymbol(self._span(class_), class_.name.name)
        self._declare_global(self.context.general.classes, symbol, class_)
        self._declare_type(symbol.name, class_)
        self.context.general.sym[class_] = symbol

        structs: list[StructSymbol] = []
        structs_by_name: dict[str, StructSymbol] = {}
        impls: list[ImplSymbol] = []
        impls_by_name: dict[str, ImplSymbol] = {}
        for member in class_.members:
            if isinstance(member, _stmt.StructUseStmt):
                struct = StructSymbol(self._span(member), member.name.name)
                self._collect_struct(symbol, struct, member, structs, structs_by_name)
                continue
            if isinstance(member, _stmt.StructDeclStmt):
                struct = StructSymbol(self._span(member), self._anonymous_name("struct", member))
                self._collect_struct(symbol, struct, member, structs, structs_by_name)
                continue
            if isinstance(member, (_stmt.ImplUseStmt, _stmt.ImplStmt)):
                name = (
                    member.interface.name
                    if isinstance(member, _stmt.ImplUseStmt)
                    else self._anonymous_name("impl", member)
                )
                impl = ImplSymbol(self._span(member), name)
                self._collect_impl(symbol, impl, member, impls, impls_by_name)

        self.context.general.struct_cls[symbol] = structs
        self.context.general.structs_by_name[symbol] = structs_by_name
        self.context.general.impl_cls[symbol] = impls
        self.context.general.impls_by_name[symbol] = impls_by_name

    def _collect_struct(
        self,
        owner: ClassSymbol,
        symbol: StructSymbol,
        node: _stmt.StructUseStmt | _stmt.StructDeclStmt,
        members: list[StructSymbol],
        by_name: dict[str, StructSymbol],
    ) -> None:
        self._declare_member(by_name, symbol, node)
        self.context.general.sym[node] = symbol
        members.append(symbol)

        if isinstance(node, _stmt.StructUseStmt):
            record = self.context.general.records.get(node.name.name)
            if record is not None:
                self.context.general.record_struct[symbol] = record
            return

        fields: list[VarSymbol] = []
        fields_by_name: dict[str, VarSymbol] = {}
        for member in node.members:
            field = VarSymbol(self._span(member), member.name.name)
            self._declare_member(fields_by_name, field, member)
            self.context.general.sym[member] = field
            if member.type is not None:
                self._schedule_binding(field, member.type, member)
            fields.append(field)
        self.context.general.member_struct[symbol] = fields
        self.context.general.struct_vars_by_name[symbol] = fields_by_name

    def _collect_impl(
        self,
        owner: ClassSymbol,
        symbol: ImplSymbol,
        node: _stmt.ImplUseStmt | _stmt.ImplStmt,
        members: list[ImplSymbol],
        by_name: dict[str, ImplSymbol],
    ) -> None:
        self._declare_member(by_name, symbol, node)
        self.context.general.sym[node] = symbol
        members.append(symbol)

        if isinstance(node, _stmt.ImplUseStmt):
            interface = self.context.general.interfaces.get(node.interface.name)
            if interface is not None:
                self.context.general.interface_impl[symbol] = interface

        definitions: list[DefSymbol] = []
        definitions_by_name: dict[str, DefSymbol] = {}
        for definition in node.members:
            definition_symbol = DefSymbol(self._span(definition), definition.name.name)
            self._declare_member(definitions_by_name, definition_symbol, definition)
            self.context.general.sym[definition] = definition_symbol
            definitions.append(definition_symbol)
            self._collect_definition_body(definition, symbol)
        self.context.general.define_impl[symbol] = definitions
        self.context.general.defs_by_name[symbol] = definitions_by_name

    def _collect_definition_body(
        self, definition: _stmt.FunctionDefStmt, owner: ImplSymbol
    ) -> None:
        for parameter in definition.parms:
            symbol = ParameterSymbol(self._span(parameter), parameter.name.name)
            self.context.general.sym[parameter] = symbol
            self._schedule_binding(symbol, parameter.type, parameter)
        self._collect_block(definition.body)

    def _schedule_binding(
        self, symbol: Symbol, type_node: _base.TypeNode, node: ASTNode
    ) -> None:
        self._pending_bindings.append((symbol, type_node, node))

    def _bind(self) -> None:
        """Materialize contracts after every declaration has been collected."""
        for symbol, type_node, node in self._pending_bindings:
            binding = self._binding_for(type_node, node)
            if isinstance(symbol, LetSymbol):
                self.context.contract.let[symbol] = binding
            elif isinstance(symbol, ParameterSymbol):
                self.context.contract.parameter[symbol] = binding
            elif isinstance(symbol, VarSymbol):
                self.context.contract.var[symbol] = binding
            else:
                raise self.error_at(ErrorCode.INTERNAL_INVALID_COLLECTED_SYMBOL, node)

    def _declare_global(
        self, table: dict[str, SymbolT], symbol: SymbolT, node: ASTNode
    ) -> None:
        if symbol.name in table:
            raise self.error_at(ErrorCode.COLLECT_DUPLICATE_DECLARATION, node, symbol.name)
        table[symbol.name] = symbol

    def _declare_member(
        self,
        table: dict[str, SymbolT],
        symbol: SymbolT,
        node: ASTNode,
    ) -> None:
        if symbol.name in table:
            raise self.error_at(ErrorCode.COLLECT_DUPLICATE_DECLARATION, node, symbol.name)
        table[symbol.name] = symbol

    def _declare_type(self, name: str, node: ASTNode) -> None:
        if name in self.context.general.types:
            raise self.error_at(ErrorCode.COLLECT_DUPLICATE_TYPE, node, name)
        self.context.general.types[name] = UserDefType()

    def _binding_for(
        self, type_node: _base.TypeNode, node: ASTNode
    ) -> Binding:
        """Build a Binding from a parsed type contract.

        Leaf types become AtomicBinding.  A container is an application of its
        outer atomic binding to recursively collected argument bindings.
        """
        match type_node:
            case _base.Name():
                return self._atomic_binding(type_node.symbol, node)
            case _base.Container():
                atomic = self._atomic_binding(type_node.base.symbol, node)
                args: list[Binding] = [
                    self._atomic_binding(argument, node) for argument in type_node.args
                ]
                return AppliedBinding(atomic, args)
            case _:
                raise self.error_at(ErrorCode.COLLECT_UNSUPPORTED_TYPE_CONTRACT, node)

    def _atomic_binding(
        self, type_syn: _base.TypeSyn, node: ASTNode
    ) -> AtomicBinding:
        type_name = type_syn.type.name
        type_def = self.context.general.types.get(type_name)
        if type_def is None:
            raise self.error_at(ErrorCode.COLLECT_UNKNOWN_TYPE, node, type_name)

        right = self.context.general.default_right
        policy = self.context.general.default_policy
        for annotation in type_syn.binding:
            annotation_name = annotation.name.name
            if annotation_name in self.context.general.rights:
                right = self.context.general.rights[annotation_name]
                continue
            if annotation_name in self.context.general.policies:
                policy = self.context.general.policies[annotation_name]
                continue
            raise self.error_at(ErrorCode.COLLECT_UNKNOWN_BINDING, node, annotation_name)
        return AtomicBinding(type_def, right, policy, type_syn.is_ref)

    def error_at(
        self, code: ErrorCode, node: ASTNode, detail: str | None = None
    ) -> KinakoCollectorError:
        message = f"[{code.code}] {code.message}"
        if detail is not None:
            message = f"{message}: {detail}"
        return KinakoCollectorError(
            message,
            node.line,
            node.col,
            self.source,
            node.len,
        )

    @staticmethod
    def _span(node: ASTNode) -> Span:
        return Span(node.line, node.col, node.len)

    @staticmethod
    def _anonymous_name(kind: str, node: ASTNode) -> str:
        return f"<{kind}@{node.line}:{node.col}>"
