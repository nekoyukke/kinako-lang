"""Resolve lexical names in a collected Kinako AST."""

from __future__ import annotations

from dataclasses import dataclass

from src.core.ast import base as _base
from src.core.ast import expr as _expr
from src.core.ast import stmt as _stmt
from src.core.ast.base import ASTNode
from src.core.context.context import Context
from src.core.scope.scope import Scope
from src.core.symbol import (
    FunctionSymbol,
    ImplSymbol,
    LetSymbol,
    ModuleSymbol,
    ParameterSymbol,
    StructSymbol,
    Symbol,
    VarSymbol,
)
from src.utils.error.resolve import KinakoResolveError
from src.utils.error.code import ErrorCode


@dataclass(frozen=True)
class ResolveResult:
    context: Context


class Resolver:
    """Resolve names while constructing temporary lexical Scopes."""

    def __init__(self, resolved_context: Context, source: str = "") -> None:
        self.context = resolved_context
        self.source = source
        self.current_scope = Scope(parent=None, symbol={})
        self.scope_depth = 0

    def resolve(self, program: _stmt.Program) -> ResolveResult:
        self.current_scope = Scope(parent=None, symbol={})
        self.scope_depth = 0

        # Top-level functions are visible to one another regardless of order.
        for statement in program.stmt:
            if isinstance(statement, _stmt.FunctionStmt):
                self._declare(self._symbol_for(statement), statement)

        for statement in program.stmt:
            self._resolve_statement(statement, top_level=True)
        return ResolveResult(self.context)

    def _resolve_statement(self, statement: _stmt.Stmt, *, top_level: bool = False) -> None:
        match statement:
            case _stmt.ImportStmt():
                self._resolve_import(statement)
            case _stmt.UnsafeStmt():
                self._resolve_statement(statement.inner, top_level=top_level)
            case _stmt.LetStmt() | _stmt.RefStmt() | _stmt.MoveStmt():
                self._resolve_local(statement)
            case _stmt.VarDeclStmt():
                self._resolve_var(statement)
            case _stmt.FunctionStmt():
                self._resolve_function(statement, already_declared=top_level)
            case _stmt.RecordDeclStmt():
                self._resolve_record(statement)
            case _stmt.InterfaceDeclStmt():
                self._resolve_interface(statement)
            case _stmt.ClassDeclStmt():
                self._resolve_class(statement)
            case _stmt.Block():
                self._resolve_block(statement)
            case _stmt.IfStmt():
                self._resolve_expr(statement.cond)
                self._resolve_statement(statement.then_block)
                if statement.else_block is not None:
                    self._resolve_statement(statement.else_block)
            case _stmt.WhileStmt():
                self._resolve_expr(statement.cond)
                self._resolve_statement(statement.block)
            case _stmt.ReturnStmt():
                self._resolve_expr(statement.value)
            case _stmt.ExprStmt():
                self._resolve_expr(statement.expr)
            case _stmt.AsmStmt():
                return
            case _:
                raise self.error_at(ErrorCode.INTERNAL_UNSUPPORTED_AST, statement)

    def _resolve_import(self, statement: _stmt.ImportStmt) -> None:
        symbol = self._symbol_for(statement)
        self._declare(symbol, statement)

    def _resolve_block(self, block: _stmt.Block) -> None:
        self._enter_scope()
        try:
            for statement in block.stmt:
                self._resolve_statement(statement)
        finally:
            self._leave_scope(block)

    def _resolve_local(
        self, statement: _stmt.LetStmt | _stmt.RefStmt | _stmt.MoveStmt
    ) -> None:
        if statement.contract is not None:
            self._resolve_type(statement.contract, statement)
        if statement.right is not None:
            self._resolve_expr(statement.right)
        self._declare(self._symbol_for(statement), statement)

    def _resolve_var(self, statement: _stmt.VarDeclStmt) -> None:
        """var の型を解決してから、通常のローカル名として登録する。"""
        if statement.type is not None:
            self._resolve_type(statement.type, statement)
        self._declare(self._symbol_for(statement), statement)

    def _resolve_function(
        self, function: _stmt.FunctionStmt, *, already_declared: bool
    ) -> None:
        if not already_declared:
            self._declare(self._symbol_for(function), function)
        self._resolve_type(function.result, function)
        self._enter_scope()
        try:
            for parameter in function.parms:
                self._resolve_parameter(parameter)
            self._resolve_block(function.body)
        finally:
            self._leave_scope(function)

    def _resolve_definition(self, definition: _stmt.FunctionDefStmt) -> None:
        self._resolve_type(definition.result, definition)
        self._enter_scope()
        try:
            for parameter in definition.parms:
                self._resolve_parameter(parameter)
            self._resolve_block(definition.body)
        finally:
            self._leave_scope(definition)

    def _resolve_parameter(self, parameter: _stmt.Parameter) -> None:
        self._resolve_type(parameter.type, parameter)
        self._declare(self._symbol_for(parameter), parameter)

    def _resolve_record(self, record: _stmt.RecordDeclStmt) -> None:
        for member in record.members:
            if isinstance(member, _stmt.VarDeclStmt) and member.type is not None:
                self._resolve_type(member.type, member)

    def _resolve_interface(self, interface: _stmt.InterfaceDeclStmt) -> None:
        for request in interface.members:
            self._resolve_type(request.result, request)
            for parameter in request.parms:
                self._resolve_parameter_type(parameter)

    def _resolve_parameter_type(self, parameter: _stmt.Parameter) -> None:
        """Validate a non-lexical parameter, such as an interface request."""
        self._resolve_type(parameter.type, parameter)

    def _resolve_class(self, class_: _stmt.ClassDeclStmt) -> None:
        for member in class_.members:
            if isinstance(member, _stmt.StructUseStmt):
                self._resolve_struct_use(member)
            elif isinstance(member, _stmt.StructDeclStmt):
                for field in member.members:
                    if field.type is not None:
                        self._resolve_type(field.type, field)
            elif isinstance(member, _stmt.ImplUseStmt):
                self._resolve_impl_use(member)
                for definition in member.members:
                    self._resolve_definition(definition)
            elif isinstance(member, _stmt.ImplStmt):
                for definition in member.members:
                    self._resolve_definition(definition)

    def _resolve_struct_use(self, struct_use: _stmt.StructUseStmt) -> None:
        record = self.context.general.records.get(struct_use.name.name)
        if record is None:
            raise self.error_at(ErrorCode.RESOLVE_UNKNOWN_RECORD, struct_use, struct_use.name.name)
        symbol = self._symbol_for(struct_use)
        if not isinstance(symbol, StructSymbol):
            raise self.error_at(ErrorCode.RESOLVE_INVALID_STRUCT_SYMBOL, struct_use)
        self.context.general.record_struct[symbol] = record

    def _resolve_impl_use(self, impl_use: _stmt.ImplUseStmt) -> None:
        interface = self.context.general.interfaces.get(impl_use.interface.name)
        if interface is None:
            raise self.error_at(ErrorCode.RESOLVE_UNKNOWN_INTERFACE, impl_use, impl_use.interface.name)
        symbol = self._symbol_for(impl_use)
        if not isinstance(symbol, ImplSymbol):
            raise self.error_at(ErrorCode.RESOLVE_INVALID_IMPL_SYMBOL, impl_use)
        self.context.general.interface_impl[symbol] = interface

    def _resolve_type(self, type_node: _base.TypeNode, node: ASTNode) -> None:
        match type_node:
            case _base.Name():
                self._resolve_type_syn(type_node.symbol, node)
            case _base.Container():
                self._resolve_type_syn(type_node.base.symbol, node)
                for argument in type_node.args:
                    self._resolve_type_syn(argument, node)
            case _:
                raise self.error_at(ErrorCode.RESOLVE_UNSUPPORTED_TYPE_CONTRACT, node)

    def _resolve_type_syn(self, type_syn: _base.TypeSyn, node: ASTNode) -> None:
        if type_syn.type.name not in self.context.general.types:
            raise self.error_at(ErrorCode.RESOLVE_UNKNOWN_TYPE, node, type_syn.type.name)
        for annotation in type_syn.binding:
            name = annotation.name.name
            if name not in self.context.general.rights and name not in self.context.general.policies:
                raise self.error_at(ErrorCode.RESOLVE_UNKNOWN_BINDING, node, name)

    def _resolve_expr(self, expression: _expr.Expr) -> None:
        match expression:
            case _expr.Variable():
                symbol = self.current_scope.look_up(expression.name.name)
                if symbol is None:
                    raise self.error_at(ErrorCode.RESOLVE_UNKNOWN_NAME, expression, expression.name.name)
                self.context.general.sym[expression] = symbol
            case _expr.MemberExpr():
                self._resolve_expr(expression.expr)
            case _expr.CallExpr():
                # callee と各引数を先に解決して、再帰呼び出しも通常の Variable として扱う。
                self._resolve_expr(expression.callee)
                for argument in expression.args:
                    self._resolve_expr(argument)
            case _expr.IndexExpr():
                self._resolve_expr(expression.expr)
                self._resolve_expr(expression.index)
            case _expr.ArithmeticExpr() | _expr.LogicExpr() | _expr.IdentityExpr() | _expr.CompExpr():
                self._resolve_expr(expression.left)
                self._resolve_expr(expression.right)
            case _expr.AssignExpr() | _expr.MoveExpr() | _expr.RefExpr():
                self._resolve_expr(expression.left)
                self._resolve_expr(expression.right)
            case _expr.ContainerImmediate():
                for value in expression.value:
                    self._resolve_expr(value)
            case _expr.Immediate():
                return
            case _:
                raise self.error_at(ErrorCode.INTERNAL_UNSUPPORTED_AST, expression)

    def _enter_scope(self) -> None:
        self.current_scope = Scope(parent=self.current_scope, symbol={})
        self.scope_depth += 1

    def _leave_scope(self, node: ASTNode) -> None:
        parent = self.current_scope.parent
        if parent is None:
            raise self.error_at(ErrorCode.INTERNAL_INVALID_SCOPE_EXIT, node)
        self.current_scope = parent
        self.scope_depth -= 1

    def _declare(self, symbol: Symbol, node: ASTNode) -> None:
        if not isinstance(
            symbol, (LetSymbol, VarSymbol, ParameterSymbol, FunctionSymbol, ModuleSymbol)
        ):
            raise self.error_at(ErrorCode.RESOLVE_INVALID_LEXICAL_SYMBOL, node)
        if symbol.name in self.current_scope.symbol:
            raise self.error_at(ErrorCode.RESOLVE_DUPLICATE_DECLARATION, node, symbol.name)
        if isinstance(symbol, VarSymbol):
            raise self.error_at(ErrorCode.RESOLVE_INVALID_LEXICAL_SYMBOL, node)
        self.current_scope.symbol[symbol.name] = symbol
        self.context.general.scope_depth[symbol] = self.scope_depth

    def _symbol_for(self, node: ASTNode) -> Symbol:
        symbol = self.context.general.sym.get(node)
        if symbol is None:
            raise self.error_at(ErrorCode.RESOLVE_MISSING_COLLECTED_SYMBOL, node)
        return symbol

    def error_at(
        self, code: ErrorCode, node: ASTNode, detail: str | None = None
    ) -> KinakoResolveError:
        message = f"[{code.code}] {code.message}"
        if detail is not None:
            message = f"{message}: {detail}"
        return KinakoResolveError(message, node.line, node.col, self.source, node.len)
