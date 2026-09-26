"""Visitor skeleton for semantic checks after name resolution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar
T = TypeVar("T")

from src.core.ast import expr as _expr
from src.core.ast import stmt as _stmt
from src.core.ast.base import ASTNode
from src.core.context.context import Context
from src.core.symbol import symbol
from src.utils.error.checker import KinakoCheckerError
from src.utils.error.code import ErrorCode
from src.core.binding.binding import *


@dataclass(frozen=True)
class CheckResult:
    context: Context

@dataclass
class ExprResult:
    binding: Binding
    sym: symbol.Symbol | None = None

class Checker:
    """Traverse a resolved program and perform semantic checks."""

    def __init__(self, checked_context: Context, source: str = "") -> None:
        self.context = checked_context
        self.source = source
        self.return_type:TypeDef
        self.moved: list[symbol.Symbol] = []
        self.binding: list[dict[symbol.Symbol, Binding]] = [] # Scope的

    def error_at(
        self, code: ErrorCode, node: ASTNode, detail: str | None = None
    ) -> KinakoCheckerError:
        message = f"[{code.code}] {code.message}"
        if detail is not None:
            message = f"{message}: {detail}"
        return KinakoCheckerError(message, node.line, node.col, self.source, node.len)

    def validate_right(self, right:Right, binding:Binding) -> bool | ErrorCode:
        match (binding):
            case AtomicBinding():
                return binding.right.access.value > right.access.value and \
                       binding.right.identity.value > right.identity.value
            case AppliedBinding():
                return self.validate_right(right, binding.atomic)
            case _:
                return ErrorCode.CHECK_UNSUPPORTED_AST

    def is_same_type(self, t1:Binding, t2:Binding) -> bool | ErrorCode:
        if type(t1) != type(t2):
            return False
        if isinstance(t1, AtomicBinding) and isinstance(t2, AtomicBinding):
            if t1.type != t2.type:
                return False
            if t1.is_ref != t2.is_ref:
                return False
            return True
        if isinstance(t1, AppliedBinding) and isinstance(t2, AppliedBinding):
            if t1.atomic.type != t2.atomic.type:
                return False
            if t1.atomic.is_ref != t2.atomic.is_ref:
                return False
            if len(t1.args) != len(t2.args):
                return False
            for i,j in zip(t1.args, t2.args):
                is_same = self.is_same_type(i,j)
                if isinstance(is_same, ErrorCode):
                    return is_same
                if not is_same:
                    return False
            return True
        return ErrorCode.CHECK_UNSUPPORTED_AST

    def unwrap_error(self, node:ASTNode, code:T|ErrorCode, message:str|None = None) -> T:
        if isinstance(code, ErrorCode):
            raise self.error_at(code, node, message)
        return code

    def get_binding_type(self, binding: Binding, node: ASTNode) -> TypeDef|ErrorCode:
        match binding:
            case AtomicBinding(type=type_):
                return type_
            case AppliedBinding(atomic=AtomicBinding(type=type_)):
                return type_
            case _:
                return ErrorCode.CHECK_UNSUPPORTED_AST

    def is_assignable(
        self,
        target: Binding,
        value: Binding,
        node: ASTNode,
    ) -> bool | ErrorCode:
        if self.is_same_type(target, value):
            return True

        target_type = self.get_binding_type(target, node)
        value_type = self.get_binding_type(value, node)
        if isinstance(target_type, ErrorCode):
            return target_type
        if isinstance(value_type, ErrorCode):
            return value_type

        match target_type, value_type:
            # 10 -> int / long / i32 ...
            case IntType(), IntegerImmediateType():
                return True

            # 1.5 -> float
            case FloatType(), DecimalImmediateType():
                return True

            # 10 -> float
            case FloatType(), IntegerImmediateType():
                return True

            case _:
                return False

    def split_right(
        self,
        source: Right,
        requested: Right,
        node: ASTNode,
    ) -> tuple[Right, Right]:
        if requested.access.value > source.access.value:
            raise self.error_at(ErrorCode.CHECK_INVALID_REFERENCE, node)
    
        if requested.identity is IdentityKind.UNIQUE:
            raise self.error_at(ErrorCode.CHECK_INVALID_REFERENCE, node)
    
        borrowed = Right(requested.access, IdentityKind.SHARED)
    
        # もともと shared なら、host 側の権限は減らさない。
        if source.identity == IdentityKind.SHARED:
            return (
                Right(source.access, IdentityKind.SHARED),
                borrowed,
            )
    
        if requested.access == AccessKind.WRITE:
            remaining_access = AccessKind.NON
        else:
            remaining_access = AccessKind.READ
    
        return (
            Right(remaining_access, IdentityKind.SHARED),
            borrowed,
        )

    def get_binding_sym(self, sym:symbol.Symbol) -> Binding | ErrorCode:
        for i in reversed(self.binding):
            if sym in i:
                return i[sym]
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
                return ErrorCode.INTERNAL_INVALID_COLLECTED_SYMBOL

    def has_interface(self, sym:symbol.InterfaceSymbol, user_type_name:str) -> bool:
        clssym = self.context.general.classes[user_type_name]
        impls = self.context.general.impl_cls[clssym]
        interfaces = [self.context.general.interface_impl[i] for i in impls if i in self.context.general.interface_impl]
        if sym in interfaces:
            return True
        return False

    def get_atomic_binding(self, binding:Binding) -> AtomicBinding | ErrorCode:
        match (binding):
            case AtomicBinding():
                return binding
            case AppliedBinding():
                return binding.atomic
            case _:
                return ErrorCode.CHECK_UNSUPPORTED_AST
    
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

    def visit_expression(self, expression: _expr.Expr) -> ExprResult:
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


    def visit_variable(self, expression: _expr.Variable) -> ExprResult:
        # this]
        sym = self.context.general.sym[expression]
        binding = self.get_binding_sym(sym)
        if isinstance(binding, ErrorCode):
            raise self.error_at(binding, expression)
        return ExprResult(
            binding,
            sym
        )

    def visit_member_expression(self, expression: _expr.MemberExpr) -> ExprResult:
        # this
        pass

    def visit_index_expression(self, expression: _expr.IndexExpr) -> ExprResult:
        # this
        pass

    def visit_arithmetic_expression(self, expression: _expr.ArithmeticExpr) -> ExprResult:
        right = self.visit_expression(expression.right)
        left = self.visit_expression(expression.left)
        right_atomic = self.get_atomic_binding(right.binding)
        left_atomic = self.get_atomic_binding(left.binding)
        if isinstance(right_atomic, ErrorCode):
            raise self.error_at(right_atomic, expression.right)
        if isinstance(left_atomic, ErrorCode):
            raise self.error_at(left_atomic, expression.left)
        # エラーチェック
        if not isinstance(right_atomic.type, IntegerImmediateType|DecimalImmediateType|IntType|FloatType):
            if not isinstance(right_atomic.type, UserDefType):
                raise self.error_at(ErrorCode.CHECK_ARITHMETIC_OPERAND_NOT_NUMERIC, expression.right)
            if not (self.has_interface(self.context.buildin.integer_impl, right_atomic.type.name) or\
               self.has_interface(self.context.buildin.decimal_impl, right_atomic.type.name)):
                raise self.error_at(ErrorCode.CHECK_CLS_NOTHAS_INTERFACE, expression.right)
            
        if not isinstance(left_atomic.type, IntegerImmediateType|DecimalImmediateType|IntType|FloatType):
            if not isinstance(left_atomic.type, UserDefType):
                raise self.error_at(ErrorCode.CHECK_ARITHMETIC_OPERAND_NOT_NUMERIC, expression.left)
            if not (self.has_interface(self.context.buildin.integer_impl, left_atomic.type.name) or\
               self.has_interface(self.context.buildin.decimal_impl, left_atomic.type.name)):
                raise self.error_at(ErrorCode.CHECK_CLS_NOTHAS_INTERFACE, expression.left)
        # Right
        if not self.unwrap_error(
            expression.left,
            self.validate_right(Right(AccessKind.READ, IdentityKind.min()), left_atomic)
        ):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.left)
        if not self.unwrap_error(
            expression.right,
            self.validate_right(Right(AccessKind.READ, IdentityKind.min()), right_atomic)
        ):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.right)
        # 暗黙的な型変換
        is_r_float = False
        if isinstance(right_atomic.type, DecimalImmediateType|FloatType):
            is_r_float = True
        if isinstance(right_atomic.type, UserDefType):
            if self.has_interface(self.context.buildin.decimal_impl, right_atomic.type.name):
                is_r_float = True

        is_l_float = False
        if isinstance(left_atomic.type, DecimalImmediateType|FloatType):
            is_l_float = True
        if isinstance(left_atomic.type, UserDefType):
            if self.has_interface(self.context.buildin.decimal_impl, left_atomic.type.name):
                is_l_float = True

        if is_l_float or is_r_float:
            # float返す
            return ExprResult(
                AtomicBinding(
                    DecimalImmediateType(),
                    self.context.general.default_right,
                    self.context.general.default_policy,
                    False
                )
            )
        return ExprResult(
            AtomicBinding(
                IntegerImmediateType(),
                self.context.general.default_right,
                self.context.general.default_policy,
                False
            )
        )

    def visit_logic_expression(self, expression: _expr.LogicExpr) -> ExprResult:
        right = self.visit_expression(expression.right)
        left = self.visit_expression(expression.left)
        # エラーチェック
        if not isinstance(right, AtomicBinding):
            raise self.error_at(ErrorCode.CHECK_LOGIC_OPERAND_NOT_BOOLEAN, expression.right, )
        if not isinstance(left, AtomicBinding):
            raise self.error_at(ErrorCode.CHECK_LOGIC_OPERAND_NOT_BOOLEAN, expression.left)
        if not isinstance(right.type, BoolType):
            raise self.error_at(ErrorCode.CHECK_LOGIC_OPERAND_NOT_BOOLEAN, expression.right)
        if not isinstance(left.type, BoolType):
            raise self.error_at(ErrorCode.CHECK_LOGIC_OPERAND_NOT_BOOLEAN, expression.left)
        # Right
        if not self.unwrap_error(
            expression.left,
            self.validate_right(Right(AccessKind.READ, IdentityKind.min()), left)
        ):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.left)
        if not self.unwrap_error(
            expression.right,
            self.validate_right(Right(AccessKind.READ, IdentityKind.min()), right)
        ):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.right)
        return ExprResult(
            AtomicBinding(
                BoolType(),
                self.context.general.default_right,
                self.context.general.default_policy,
                False
            )
        )

    def visit_identity_expression(self, expression: _expr.IdentityExpr) -> ExprResult:
        right = self.visit_expression(expression.right)
        left = self.visit_expression(expression.left)
        right_atomic = self.get_atomic_binding(right.binding)
        left_atomic = self.get_atomic_binding(left.binding)
        if isinstance(right_atomic, ErrorCode):
            raise self.error_at(right_atomic, expression.right)
        if isinstance(left_atomic, ErrorCode):
            raise self.error_at(left_atomic, expression.left)
        # エラーチェック
        if right_atomic.type != left_atomic.type:
            raise self.error_at(ErrorCode.CHECK_IDENTITY_OPERAND_TYPE_MISMATCH, expression)
        if isinstance(right_atomic.type, UserDefType):
            if not self.has_interface(self.context.buildin.identity_impl, right_atomic.type.name):
                raise self.error_at(ErrorCode.CHECK_CLS_NOTHAS_INTERFACE, expression.right)
        if isinstance(left_atomic.type, UserDefType):
            if not self.has_interface(self.context.buildin.identity_impl, left_atomic.type.name):
                raise self.error_at(ErrorCode.CHECK_CLS_NOTHAS_INTERFACE, expression.left)
        # Right
        if not self.unwrap_error(
            expression.left,
            self.validate_right(Right(AccessKind.READ, IdentityKind.min()), left_atomic)
        ):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.left)
        if not self.unwrap_error(
            expression.right,
            self.validate_right(Right(AccessKind.READ, IdentityKind.min()), right_atomic)
        ):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.right)
        return ExprResult(
            AtomicBinding(
                BoolType(),
                self.context.general.default_right,
                self.context.general.default_policy,
                False
            )
        )

    def visit_comparison_expression(self, expression: _expr.CompExpr) -> ExprResult:
        right = self.visit_expression(expression.right)
        left = self.visit_expression(expression.left)
        right_atomic = self.get_atomic_binding(right.binding)
        left_atomic = self.get_atomic_binding(left.binding)
        if isinstance(right_atomic, ErrorCode):
            raise self.error_at(right_atomic, expression.right)
        if isinstance(left_atomic, ErrorCode):
            raise self.error_at(left_atomic, expression.left)
        # エラーチェック
        if right_atomic.type != left_atomic.type:
            raise self.error_at(ErrorCode.CHECK_IDENTITY_OPERAND_TYPE_MISMATCH, expression)
        if isinstance(right_atomic.type, UserDefType):
            if not self.has_interface(self.context.buildin.identity_impl, right_atomic.type.name):
                raise self.error_at(ErrorCode.CHECK_CLS_NOTHAS_INTERFACE, expression.right)
        if isinstance(left_atomic.type, UserDefType):
            if not self.has_interface(self.context.buildin.identity_impl, left_atomic.type.name):
                raise self.error_at(ErrorCode.CHECK_CLS_NOTHAS_INTERFACE, expression.left)
        # Right
        if not self.unwrap_error(
            expression.left,
            self.validate_right(Right(AccessKind.READ, IdentityKind.min()), left_atomic)
        ):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.left)
        if not self.unwrap_error(
            expression.right,
            self.validate_right(Right(AccessKind.READ, IdentityKind.min()), right_atomic)
        ):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.right)
        return ExprResult(
            AtomicBinding(
                BoolType(),
                self.context.general.default_right,
                self.context.general.default_policy,
                False
            )
        )

    def visit_assign_expression(self, expression: _expr.AssignExpr) -> ExprResult:
        # this
        pass

    def visit_move_expression(self, expression: _expr.MoveExpr) -> ExprResult:
        # this
        pass

    def visit_ref_expression(self, expression: _expr.RefExpr) -> ExprResult:
        # this
        pass

    def visit_container_immediate(self, expression: _expr.ContainerImmediate) -> ExprResult:
        # this
        pass

    def visit_string_immediate(self, expression: _expr.StringImmediate) -> ExprResult:
        # this
        pass

    def visit_integer_immediate(self, expression: _expr.IntegerImmediate) -> ExprResult:
        # this
        pass

    def visit_decimal_immediate(self, expression: _expr.DecimalImmediate) -> ExprResult:
        # this
        pass

    def visit_none_immediate(self, expression: _expr.NoneImmediate) -> ExprResult:
        # this
        pass

    def visit_null_immediate(self, expression: _expr.NullImmediate) -> ExprResult:
        # this
        pass
