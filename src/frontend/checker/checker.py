"""Visitor skeleton for semantic checks after name resolution."""

from __future__ import annotations

from dataclasses import dataclass

from src.core.ast import base as _base
from src.core.ast import expr as _expr
from src.core.ast import stmt as _stmt
from src.core.ast.base import ASTNode
from src.core.context.context import context
from src.core.symbol import symbol
from src.utils.error.checker import KinakoCheckerError
from src.utils.error.code import ErrorCode
from src.core.binding.binding import *


@dataclass(frozen=True)
class CheckResult:
    context: context

class Checker:
    """Traverse a resolved program and perform semantic checks."""

    def __init__(self, checked_context: context, source: str = "") -> None:
        self.context = checked_context
        self.source = source
        self.return_type:TypeDef

    def check(self, program: _stmt.Program) -> CheckResult:
        # this
        self.visit_program(program)
        return CheckResult(self.context)

    def visit_program(self, program: _stmt.Program) -> None:
        # this
        for statement in program.stmt:
            self.visit_statement(statement)

    def visit_statement(self, statement: _stmt.Stmt) -> bool:
        # this
        match statement:
            case _stmt.LetStmt():
                return self.visit_let_statement(statement)
            case _stmt.RefStmt():
                return self.visit_ref_statement(statement)
            case _stmt.MoveStmt():
                return self.visit_move_statement(statement)
            case _stmt.VarDeclStmt():
                return self.visit_var_declaration(statement)
            case _stmt.FunctionStmt():
                return self.visit_function_statement(statement)
            case _stmt.FunctionDefStmt():
                return self.visit_function_definition(statement)
            case _stmt.FunctionRequestStmt():
                return self.visit_function_request(statement)
            case _stmt.RecordDeclStmt():
                return self.visit_record_declaration(statement)
            case _stmt.InterfaceDeclStmt():
                return self.visit_interface_declaration(statement)
            case _stmt.ClassDeclStmt():
                return self.visit_class_declaration(statement)
            case _stmt.Block():
                return self.visit_block(statement)
            case _stmt.IfStmt():
                return self.visit_if_statement(statement)
            case _stmt.WhileStmt():
                return self.visit_while_statement(statement)
            case _stmt.ReturnStmt():
                return self.visit_return_statement(statement)
            case _stmt.ExprStmt():
                self.visit_expression(statement.expr)
                return False
            case _:
                raise self.error_at(ErrorCode.CHECK_UNSUPPORTED_AST, statement)

    def visit_let_statement(self, statement: _stmt.LetStmt) -> bool:
        # this
        pass

    def visit_ref_statement(self, statement: _stmt.RefStmt) -> bool:
        # this
        pass

    def visit_move_statement(self, statement: _stmt.MoveStmt) -> bool:
        # this
        pass

    def visit_var_declaration(self, statement: _stmt.VarDeclStmt) -> bool:
        # this
        pass

    def visit_function_statement(self, statement: _stmt.FunctionStmt) -> bool:
        # this
        pass

    def visit_function_definition(self, statement: _stmt.FunctionDefStmt) -> bool:
        # this
        pass

    def visit_function_request(self, statement: _stmt.FunctionRequestStmt) -> bool:
        # this
        pass

    def visit_parameter(self, parameter: _stmt.Parameter) -> None:
        # this
        pass

    def visit_record_declaration(self, statement: _stmt.RecordDeclStmt) -> bool:
        # this
        pass

    def visit_interface_declaration(self, statement: _stmt.InterfaceDeclStmt) -> bool:
        # this
        pass

    def visit_class_declaration(self, statement: _stmt.ClassDeclStmt) -> bool:
        # this
        pass

    def visit_class_member(self, member: _stmt.ClassMemberStmt) -> bool:
        # this
        pass

    def visit_struct_use(self, statement: _stmt.StructUseStmt) -> bool:
        # this
        pass

    def visit_struct_declaration(self, statement: _stmt.StructDeclStmt) -> bool:
        # this
        pass

    def visit_impl_use(self, statement: _stmt.ImplUseStmt) -> bool:
        # this
        pass

    def visit_impl(self, statement: _stmt.ImplStmt) -> bool:
        # this
        pass

    def visit_block(self, block: _stmt.Block) -> bool:
        # this
        pass

    def visit_if_statement(self, statement: _stmt.IfStmt) -> bool:
        # this
        pass

    def visit_while_statement(self, statement: _stmt.WhileStmt) -> bool:
        # this
        pass

    def visit_return_statement(self, statement: _stmt.ReturnStmt) -> bool:
        # this
        pass

    def visit_expression(self, expression: _expr.Expr) -> Binding:
        # this
        match expression:
            case _expr.Variable():
                return self.visit_variable(expression)
            case _expr.MemberExpr():
                return self.visit_member_expression(expression)
            case _expr.IndexExpr():
                return self.visit_index_expression(expression)
            case _expr.ArithmeticExpr():
                return self.visit_arithmetic_expression(expression)
            case _expr.LogicExpr():
                return self.visit_logic_expression(expression)
            case _expr.IdentityExpr():
                return self.visit_identity_expression(expression)
            case _expr.CompExpr():
                return self.visit_comparison_expression(expression)
            case _expr.AssignExpr():
                return self.visit_assign_expression(expression)
            case _expr.MoveExpr():
                return self.visit_move_expression(expression)
            case _expr.RefExpr():
                return self.visit_ref_expression(expression)
            case _expr.ContainerImmediate():
                return self.visit_container_immediate(expression)
            case _expr.StringImmediate():
                return self.visit_string_immediate(expression)
            case _expr.IntegerImmediate():
                return self.visit_integer_immediate(expression)
            case _expr.DecimalImmediate():
                return self.visit_decimal_immediate(expression)
            case _expr.NoneImmediate():
                return self.visit_none_immediate(expression)
            case _expr.NullImmediate():
                return self.visit_null_immediate(expression)
            case _:
                raise self.error_at(ErrorCode.CHECK_UNSUPPORTED_AST, expression)

    def error_at(
        self, code: ErrorCode, node: ASTNode, detail: str | None = None
    ) -> KinakoCheckerError:
        message = f"[{code.code}] {code.message}"
        if detail is not None:
            message = f"{message}: {detail}"
        return KinakoCheckerError(message, node.line, node.col, self.source, node.len)

    def visit_variable(self, expression: _expr.Variable) -> Binding:
        # this]
        sym = self.context.general.sym[expression]
        match (sym):
            case symbol.LetSymbol():
                return self.context.contract.let[sym]
            case symbol.VarSymbol():
                return self.context.contract.var[sym]
            case symbol.DefSymbol():
                return self.context.contract.define[sym]
            case symbol.FunctionSymbol():
                return self.context.contract.function[sym]
            case symbol.ParameterSymbol():
                return self.context.contract.parameter[sym]
            case symbol.RQSymbol():
                return self.context.contract.rq[sym]
            case _:
                raise self.error_at(ErrorCode.INTERNAL_INVALID_COLLECTED_SYMBOL, expression)

    def visit_member_expression(self, expression: _expr.MemberExpr) -> Binding:
        # this
        pass

    def visit_index_expression(self, expression: _expr.IndexExpr) -> Binding:
        # this
        pass

    def visit_arithmetic_expression(self, expression: _expr.ArithmeticExpr) -> Binding:
        # this
        right = self.visit_expression(expression.right)
        left = self.visit_expression(expression.left)
        if not isinstance(right, AtomicBinding):
            raise self.error_at(ErrorCode.CHECK_GENERIC_ARITHMETIC, expression.right)
        if not isinstance(left, AtomicBinding):
            # this
            pass

    def visit_logic_expression(self, expression: _expr.LogicExpr) -> Binding:
        # this
        pass

    def visit_identity_expression(self, expression: _expr.IdentityExpr) -> Binding:
        # this
        pass

    def visit_comparison_expression(self, expression: _expr.CompExpr) -> Binding:
        # this
        pass

    def visit_assign_expression(self, expression: _expr.AssignExpr) -> Binding:
        # this
        pass

    def visit_move_expression(self, expression: _expr.MoveExpr) -> Binding:
        # this
        pass

    def visit_ref_expression(self, expression: _expr.RefExpr) -> Binding:
        # this
        pass

    def visit_container_immediate(self, expression: _expr.ContainerImmediate) -> Binding:
        # this
        pass

    def visit_string_immediate(self, expression: _expr.StringImmediate) -> Binding:
        # this
        pass

    def visit_integer_immediate(self, expression: _expr.IntegerImmediate) -> Binding:
        # this
        pass

    def visit_decimal_immediate(self, expression: _expr.DecimalImmediate) -> Binding:
        # this
        pass

    def visit_none_immediate(self, expression: _expr.NoneImmediate) -> Binding:
        # this
        pass

    def visit_null_immediate(self, expression: _expr.NullImmediate) -> Binding:
        # this
        pass
