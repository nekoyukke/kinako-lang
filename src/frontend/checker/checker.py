"""名前解決後の意味検査を行う visitor。"""

from __future__ import annotations

from dataclasses import dataclass

from src.core.ast import base as _base
from src.core.ast import expr as _expr
from src.core.ast import stmt as _stmt
from src.core.ast.base import ASTNode
from src.core.context.context import context
from src.core.symbol import symbol
from src.core.symbol.symbol import Symbol
from src.utils.error.code import ErrorCode
from src.utils.error.checker import KinakoCheckerError
from src.core.binding.binding import *


@dataclass(frozen=True)
class CheckResult:
    context: context


@dataclass(frozen=True)
class ExprResult:
    binding: Binding
    # 現在は変数そのものだけが ref / move の対象になる。
    variable: Symbol | None = None
    # Member/Index を含めた値を所有する root 変数。部分 ref の寿命判定に使う。
    root: Symbol | None = None
    # Class の def を MemberExpr から呼ぶとき、宣言済み第1引数と照合する対象。
    receiver: ExprResult | None = None


@dataclass(frozen=True)
class Place:
    """将来の部分 ref / field move のための場所記述子。

    現行仕様では field/index の ref は root 単位で追跡するため、Checker は
    この型を使わず Symbol とスコープ深さだけで状態を追跡する。
    """

    root: Symbol
    projections: tuple[object, ...] = ()

    @property
    def key(self) -> tuple[object, ...]:
        """フロー中の Binding/Right 状態を区別する安定した場所キー。"""
        return (self.root, *self.projections)


@dataclass(frozen=True)
class Loan:
    """block の終了時に復元する借用 Right を表す。"""

    host: Symbol
    target_root: Symbol
    ref: Symbol | None
    restore: Right


class Checker:
    """名前解決済みプログラムを走査して意味検査を行う。"""

    def __init__(self, checked_context: context, source: str = "") -> None:
        self.context = checked_context
        self.source = source
        # field/index は root の状態を共有し、投影経路ごとの状態は持たない。
        self.binding_state: dict[Symbol, Binding] = {}
        self.right_state: dict[Symbol, Right] = {}
        self.return_types: list[Binding] = []
        self.loans: list[list[Loan]] = []
        # Place を使わない代わりに、root ごとに同時 field ref を禁止する。
        self.active_reference_roots: set[Symbol] = set()
        # 現在の制御フローで実行済みの move。分岐を合流するときに照合する。
        self.move_edges: list[tuple[Symbol, Symbol]] = []

    def check(self, program: _stmt.Program) -> CheckResult:
        self.loans.append([])
        try:
            self.visit_program(program)
        finally:
            for loan in reversed(self.loans.pop()):
                self.restore_right(
                    loan.host, loan.target_root, loan.ref, loan.restore
                )
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
        """let の初期値を読み取り、宣言 Binding または推論 Binding を登録する。"""
        sym = self.context.general.sym.get(statement)
        if sym is None:
            raise self.error_at(ErrorCode.CHECK_UNKNOWN_SYMBOL, statement)

        if statement.contract is None:
            if statement.right is None:
                raise self.error_at(ErrorCode.CHECK_MISSING_BINDING, statement)
            value = self.visit_expression(statement.right)
            self.require_result_right(
                value, Right(AccessKind.READ, IdentityKind.SHARED), statement.right
            )
            self.set_binding(sym, value.binding)
            return False

        binding = self.binding_of(sym, statement)
        if self.is_reference(binding, statement):
            raise self.error_at(
                ErrorCode.CHECK_REFERENCE_INITIALIZER_REQUIRED, statement
            )
        if statement.right is not None:
            value = self.visit_expression(statement.right)
            self.require_result_right(
                value, Right(AccessKind.READ, IdentityKind.SHARED), statement.right
            )
            if not self.is_assignable(binding, value.binding, statement):
                raise self.error_at(ErrorCode.CHECK_ASSIGNMENT_TYPE_MISMATCH, statement)
        self.set_binding(sym, binding)
        return False

    def visit_ref_statement(self, statement: _stmt.RefStmt) -> bool:
        """新しい変数へ、別の単純変数からの ref を束縛する。"""
        target = self.context.general.sym.get(statement)
        if target is None:
            raise self.error_at(ErrorCode.CHECK_UNKNOWN_SYMBOL, statement)
        if statement.right is None:
            raise self.error_at(ErrorCode.CHECK_MISSING_INITIALIZER, statement)
        source = self.visit_expression(statement.right)
        if statement.contract is not None:
            target_binding = self.binding_of(target, statement)
            if not self.is_reference(target_binding, statement):
                raise self.error_at(
                    ErrorCode.CHECK_REFERENCE_TARGET_NOT_REFERENCE, statement
                )
        else:
            target_binding = source.binding
        if not self.has_same_type(target_binding, source.binding, statement):
            raise self.error_at(ErrorCode.CHECK_ASSIGNMENT_TYPE_MISMATCH, statement)

        reference_binding, remaining, borrowed, source_right = self.borrow_reference(
            source,
            target_binding,
            Right(AccessKind.READ, IdentityKind.SHARED),
            statement.right,
            statement,
        )
        if source.variable is None:
            raise self.error_at(ErrorCode.CHECK_INVALID_REFERENCE, statement)
        target_root = self.require_reference_target(
            ExprResult(reference_binding, target, target), source, statement
        )
        self.set_binding(target, reference_binding)
        self.active_reference_roots.add(target_root)
        self.apply_right_split(source.variable, target, remaining, borrowed)
        self.loans[-1].append(
            Loan(source.variable, target_root, target, source_right)
        )
        return False

    def visit_move_statement(self, statement: _stmt.MoveStmt) -> bool:
        """新しい変数へ、別の単純変数の所有権を move する。"""
        target = self.context.general.sym.get(statement)
        if target is None:
            raise self.error_at(ErrorCode.CHECK_UNKNOWN_SYMBOL, statement)
        if statement.right is None:
            raise self.error_at(ErrorCode.CHECK_MISSING_INITIALIZER, statement)
        source = self.visit_expression(statement.right)
        self.require_movable_source(source, statement.right, statement)

        if statement.contract is not None:
            contract = self.binding_of(target, statement)
            if self.is_reference(contract, statement):
                raise self.error_at(ErrorCode.CHECK_REFERENCE_MOVE_FORBIDDEN, statement)
            if not self.has_same_type(contract, source.binding, statement):
                raise self.error_at(ErrorCode.CHECK_ASSIGNMENT_TYPE_MISMATCH, statement)

        # move は source の Binding をそのまま引き継ぐ。宣言 contract は型検査だけ。
        self.set_binding(target, source.binding)
        assert source.variable is not None
        self.set_available_right(
            source.variable, Right(AccessKind.NON, IdentityKind.SHARED)
        )
        self.move_edges.append((source.variable, target))
        return False

    def visit_var_declaration(self, statement: _stmt.VarDeclStmt) -> bool:
        """var は Collector 済みの型契約を持つだけで、初期化はしない。"""
        return False

    def visit_function_statement(self, statement: _stmt.FunctionStmt) -> bool:
        """本体を検査する。収集済みシグネチャにより再帰呼び出しも解決済み。"""
        sym = self.context.general.sym.get(statement)
        if not isinstance(sym, symbol.FunctionSymbol):
            raise self.error_at(ErrorCode.CHECK_UNKNOWN_SYMBOL, statement)
        return self.visit_callable(sym, statement.parms, statement.body, statement)

    def visit_function_definition(self, statement: _stmt.FunctionDefStmt) -> bool:
        """impl 内 def の本体を検査し、同じ def への再帰呼び出しも許可する。"""
        sym = self.context.general.sym.get(statement)
        if not isinstance(sym, symbol.DefSymbol):
            raise self.error_at(ErrorCode.CHECK_UNKNOWN_SYMBOL, statement)
        return self.visit_callable(sym, statement.parms, statement.body, statement)

    def visit_callable(
        self,
        sym: Symbol,
        parameters: list[_stmt.Parameter],
        body: _stmt.Block,
        node: ASTNode,
    ) -> bool:
        """トップレベル関数と impl def に共通の本体・return 検査。"""
        signature = self.binding_of(sym, node)
        match signature:
            case AppliedBinding(
                atomic=AtomicBinding(type=FunctionType()), args=[result, *_]
            ):
                pass
            case _:
                raise self.error_at(ErrorCode.CHECK_MISSING_BINDING, node)

        # 関数ローカルの Binding/Right は、次の関数や呼び出し元へ漏らさない。
        saved_bindings = self.binding_state.copy()
        saved_rights = self.right_state.copy()
        saved_active_references = self.active_reference_roots.copy()
        saved_moves = list(self.move_edges)
        self.return_types.append(result)
        try:
            for parameter in parameters:
                self.visit_parameter(parameter)
            if not self.visit_block(body):
                raise self.error_at(ErrorCode.CHECK_MISSING_RETURN, node)
        finally:
            self.return_types.pop()
            self.binding_state = saved_bindings
            self.right_state = saved_rights
            self.active_reference_roots = saved_active_references
            self.move_edges = saved_moves
        return False

    def visit_function_request(self, statement: _stmt.FunctionRequestStmt) -> bool:
        """rq の本体は無い。Collector 済みシグネチャを impl use で照合する。"""
        return False

    def visit_parameter(self, parameter: _stmt.Parameter) -> None:
        """関数本体中の引数名を、収集済みの宣言 Binding として登録する。"""
        sym = self.context.general.sym.get(parameter)
        if not isinstance(sym, symbol.ParameterSymbol):
            raise self.error_at(ErrorCode.CHECK_UNKNOWN_SYMBOL, parameter)
        self.set_binding(sym, self.binding_of(sym, parameter))

    def visit_record_declaration(self, statement: _stmt.RecordDeclStmt) -> bool:
        """Record のフィールド契約は Collector 済みなので、ここでは本体を持たない。"""
        return False

    def visit_interface_declaration(self, statement: _stmt.InterfaceDeclStmt) -> bool:
        for request in statement.members:
            self.visit_function_request(request)
        return False

    def visit_class_declaration(self, statement: _stmt.ClassDeclStmt) -> bool:
        """Class に属する impl を走査し、def 本体も通常関数と同様に検査する。"""
        for member in statement.members:
            self.visit_class_member(member)
        return False

    def visit_class_member(self, member: _stmt.ClassMemberStmt) -> bool:
        match member:
            case _stmt.StructUseStmt():
                return self.visit_struct_use(member)
            case _stmt.StructDeclStmt():
                return self.visit_struct_declaration(member)
            case _stmt.ImplUseStmt():
                return self.visit_impl_use(member)
            case _stmt.ImplStmt():
                return self.visit_impl(member)
            case _:
                raise self.error_at(ErrorCode.CHECK_UNSUPPORTED_AST, member)

    def visit_struct_use(self, statement: _stmt.StructUseStmt) -> bool:
        return False

    def visit_struct_declaration(self, statement: _stmt.StructDeclStmt) -> bool:
        return False

    def visit_impl_use(self, statement: _stmt.ImplUseStmt) -> bool:
        """Interface の rq と、この impl の def を名前・型・戻り値まで照合する。"""
        impl = self.context.general.sym.get(statement)
        if not isinstance(impl, symbol.ImplSymbol):
            raise self.error_at(ErrorCode.CHECK_UNKNOWN_SYMBOL, statement)
        interface = self.context.general.interface_impl.get(impl)
        if interface is None:
            raise self.error_at(ErrorCode.CHECK_UNKNOWN_INTERFACE_REQUEST, statement)

        requests = self.context.general.rqs_by_name.get(interface, {})
        definitions = self.context.general.defs_by_name.get(impl, {})
        for name, request in requests.items():
            definition = definitions.get(name)
            if definition is None:
                raise self.error_at(ErrorCode.CHECK_IMPL_MISSING_DEFINITION, statement, name)
            self.require_implementation_signature(
                self.binding_of(request, statement),
                self.binding_of(definition, statement),
                statement,
                name,
            )

        for name in definitions:
            if name not in requests:
                raise self.error_at(
                    ErrorCode.CHECK_IMPL_UNEXPECTED_DEFINITION, statement, name
                )
        for definition in statement.members:
            self.visit_function_definition(definition)
        return False

    def require_implementation_signature(
        self, request: Binding, definition: Binding, node: ASTNode, name: str
    ) -> None:
        """rq と def を比較する。def の明示 receiver は rq には含めない。"""
        match request, definition:
            case (
                AppliedBinding(
                    atomic=AtomicBinding(type=FunctionType()),
                    args=[request_result, *request_parameters],
                ),
                AppliedBinding(
                    atomic=AtomicBinding(type=FunctionType()),
                    args=[definition_result, _receiver, *definition_parameters],
                ),
            ):
                pass
            case _:
                raise self.error_at(ErrorCode.CHECK_MISSING_BINDING, node)

        if len(request_parameters) != len(definition_parameters):
            raise self.error_at(
                ErrorCode.CHECK_IMPL_PARAMETER_COUNT_MISMATCH, node, name
            )
        if any(
            not self.has_same_type(request_parameter, definition_parameter, node)
            for request_parameter, definition_parameter in zip(
                request_parameters, definition_parameters
            )
        ):
            raise self.error_at(
                ErrorCode.CHECK_IMPL_PARAMETER_TYPE_MISMATCH, node, name
            )
        if not self.has_same_type(request_result, definition_result, node):
            raise self.error_at(ErrorCode.CHECK_IMPL_RETURN_TYPE_MISMATCH, node, name)

    def visit_impl(self, statement: _stmt.ImplStmt) -> bool:
        for definition in statement.members:
            self.visit_function_definition(definition)
        return False

    def visit_block(self, block: _stmt.Block) -> bool:
        self.loans.append([])
        try:
            for statement in block.stmt:
                if self.visit_statement(statement):
                    return True
            return False
        finally:
            for loan in reversed(self.loans.pop()):
                self.restore_right(
                    loan.host, loan.target_root, loan.ref, loan.restore
                )

    def visit_if_statement(self, statement: _stmt.IfStmt) -> bool:
        """bool 条件の両分岐を検査し、move の経路差を拒否して合流する。"""
        self.require_boolean_condition(statement.cond)
        prefix_length = len(self.move_edges)
        then_returns, then_bindings, then_rights, then_moves = (
            self.visit_isolated_statement(statement.then_block)
        )
        if statement.else_block is None:
            else_returns, else_bindings, else_rights, else_moves = (
                False,
                self.binding_state.copy(),
                self.right_state.copy(),
                list(self.move_edges),
            )
        else:
            else_returns, else_bindings, else_rights, else_moves = (
                self.visit_isolated_statement(statement.else_block)
            )

        then_delta = then_moves[prefix_length:]
        else_delta = else_moves[prefix_length:]
        if then_delta != else_delta:
            raise self.error_at(ErrorCode.CHECK_CONDITIONAL_MOVE_MISMATCH, statement)

        # 両経路が同一の move を行う場合だけ、その元・先の状態を外へ反映する。
        self.merge_move_state(then_delta, then_bindings, then_rights)
        self.move_edges.extend(then_delta)
        return then_returns and else_returns

    def visit_while_statement(self, statement: _stmt.WhileStmt) -> bool:
        """while は 0 回実行の経路があるため、条件付き move を許さない。"""
        self.require_boolean_condition(statement.cond)
        prefix_length = len(self.move_edges)
        _, _, _, moves = self.visit_isolated_statement(statement.block)
        if moves[prefix_length:]:
            raise self.error_at(ErrorCode.CHECK_CONDITIONAL_MOVE_MISMATCH, statement)
        return False

    def require_boolean_condition(self, condition: _expr.Expr) -> None:
        """条件式が読める bool 値であることを検査する。"""
        value = self.visit_expression(condition)
        self.require_result_right(
            value, Right(AccessKind.READ, IdentityKind.SHARED), condition
        )
        if not isinstance(self.binding_type(value.binding, condition), BoolType):
            raise self.error_at(ErrorCode.CHECK_CONDITION_NOT_BOOLEAN, condition)

    def visit_isolated_statement(
        self, statement: _stmt.Stmt
    ) -> tuple[bool, dict[Symbol, Binding], dict[Symbol, Right], list[tuple[Symbol, Symbol]]]:
        """分岐・ループ本体を検査し、合流用の状態を返してから復元する。"""
        saved_bindings = self.binding_state.copy()
        saved_rights = self.right_state.copy()
        saved_loans = [list(loans) for loans in self.loans]
        saved_active_references = self.active_reference_roots.copy()
        saved_moves = list(self.move_edges)
        try:
            return (
                self.visit_statement(statement),
                self.binding_state.copy(),
                self.right_state.copy(),
                list(self.move_edges),
            )
        finally:
            self.binding_state = saved_bindings
            self.right_state = saved_rights
            self.loans = saved_loans
            self.active_reference_roots = saved_active_references
            self.move_edges = saved_moves

    def merge_move_state(
        self,
        moves: list[tuple[Symbol, Symbol]],
        bindings: dict[Symbol, Binding],
        rights: dict[Symbol, Right],
    ) -> None:
        """両分岐で一致した move に関係する状態だけを合流する。"""
        for variable in {symbol for edge in moves for symbol in edge}:
            if variable in bindings:
                self.binding_state[variable] = bindings[variable]
            else:
                self.binding_state.pop(variable, None)
            if variable in rights:
                self.right_state[variable] = rights[variable]
            else:
                self.right_state.pop(variable, None)

    def visit_return_statement(self, statement: _stmt.ReturnStmt) -> bool:
        """return 値を現在検査中の関数の宣言戻り値と照合する。"""
        if not self.return_types:
            raise self.error_at(ErrorCode.CHECK_RETURN_OUTSIDE_FUNCTION, statement)
        value = self.visit_expression(statement.value)
        self.require_result_right(
            value,
            Right(AccessKind.READ, IdentityKind.SHARED),
            statement.value,
        )
        if not self.is_assignable(self.return_types[-1], value.binding, statement):
            raise self.error_at(ErrorCode.CHECK_RETURN_TYPE_MISMATCH, statement)
        return True

    def visit_expression(self, expression: _expr.Expr) -> ExprResult:
        # this
        match expression:
            case _expr.Variable():
                result = self.visit_variable(expression)
            case _expr.MemberExpr():
                result = self.visit_member_expression(expression)
            case _expr.CallExpr():
                result = self.visit_call_expression(expression)
            case _expr.IndexExpr():
                result = self.visit_index_expression(expression)
            case _expr.ArithmeticExpr():
                result = self.visit_arithmetic_expression(expression)
            case _expr.LogicExpr():
                result = self.visit_logic_expression(expression)
            case _expr.IdentityExpr():
                result = self.visit_identity_expression(expression)
            case _expr.CompExpr():
                result = self.visit_comparison_expression(expression)
            case _expr.AssignExpr():
                result = self.visit_assign_expression(expression)
            case _expr.MoveExpr():
                result = self.visit_move_expression(expression)
            case _expr.RefExpr():
                result = self.visit_ref_expression(expression)
            case _expr.ContainerImmediate():
                result = self.visit_container_immediate(expression)
            case _expr.StringImmediate():
                result = self.visit_string_immediate(expression)
            case _expr.IntegerImmediate():
                result = self.visit_integer_immediate(expression)
            case _expr.DecimalImmediate():
                result = self.visit_decimal_immediate(expression)
            case _expr.NoneImmediate():
                result = self.visit_none_immediate(expression)
            case _expr.NullImmediate():
                result = self.visit_null_immediate(expression)
            case _:
                raise self.error_at(ErrorCode.CHECK_UNSUPPORTED_AST, expression)
        self.context.general.binding[expression] = result.binding
        return result

    def error_at(
        self, code: ErrorCode, node: ASTNode, detail: str | None = None
    ) -> KinakoCheckerError:
        message = f"[{code.code}] {code.message}"
        if detail is not None:
            message = f"{message}: {detail}"
        return KinakoCheckerError(message, node.line, node.col, self.source, node.len)

    def binding_of(self, sym: Symbol, node: ASTNode) -> Binding:
        """名前解決済み Symbol の宣言 Binding を返す。"""
        binding = self.binding_state.get(sym)
        if binding is not None:
            return binding
        match sym:
            case symbol.LetSymbol():
                binding = self.context.contract.let.get(sym)
            case symbol.VarSymbol():
                binding = self.context.contract.var.get(sym)
            case symbol.DefSymbol():
                binding = self.context.contract.define.get(sym)
            case symbol.FunctionSymbol():
                binding = self.context.contract.function.get(sym)
            case symbol.ParameterSymbol():
                binding = self.context.contract.parameter.get(sym)
            case symbol.RQSymbol():
                binding = self.context.contract.rq.get(sym)
            case _:
                raise self.error_at(ErrorCode.CHECK_UNKNOWN_SYMBOL, node)
        if binding is None:
            raise self.error_at(ErrorCode.CHECK_MISSING_BINDING, node)
        return binding

    def set_binding(self, sym: Symbol, binding: Binding) -> None:
        """root 変数のフロー中 Binding を設定する。"""
        self.binding_state[sym] = binding

    def effective_binding(
        self, variable: Symbol, binding: Binding, node: ASTNode
    ) -> Binding:
        """変数の現在の Right を反映した Binding のコピーを返す。"""
        binding = self.binding_state.get(variable, binding)
        right = self.available_right(variable, binding, node)
        if isinstance(binding, AtomicBinding):
            return AtomicBinding(binding.type, right, binding.policy, binding.is_ref)
        if isinstance(binding, AppliedBinding):
            atomic = binding.atomic
            return AppliedBinding(
                AtomicBinding(atomic.type, right, atomic.policy, atomic.is_ref),
                list(binding.args),
            )
        raise self.error_at(ErrorCode.CHECK_UNSUPPORTED_AST, node)

    def available_right(self, variable: Symbol, binding: Binding, node: ASTNode) -> Right:
        """Context を変更せず、現在のフロー上の Right を返す。"""
        right = self.right_state.get(variable)
        if right is None:
            right = self.binding_right(binding, node)
        return Right(right.access, right.identity)

    def binding_right(self, binding: Binding, node: ASTNode) -> Right:
        """Binding に記録された Right を返す。"""
        match binding:
            case AtomicBinding(right=right):
                return right
            case AppliedBinding(atomic=AtomicBinding(right=right)):
                return right
            case _:
                raise self.error_at(ErrorCode.CHECK_UNSUPPORTED_AST, node)

    def binding_type(self, binding: Binding, node: ASTNode) -> TypeDef:
        """Binding に記録された Type を返す。"""
        match binding:
            case AtomicBinding(type=type_):
                return type_
            case AppliedBinding(atomic=AtomicBinding(type=type_)):
                return type_
            case _:
                raise self.error_at(ErrorCode.CHECK_UNSUPPORTED_AST, node)

    def is_reference(self, binding: Binding, node: ASTNode) -> bool:
        """Binding が参照型として宣言されているか返す。"""
        match binding:
            case AtomicBinding(is_ref=is_ref):
                return is_ref
            case AppliedBinding(atomic=AtomicBinding(is_ref=is_ref)):
                return is_ref
            case _:
                raise self.error_at(ErrorCode.CHECK_UNSUPPORTED_AST, node)

    def as_reference(
        self, binding: Binding, right: Right, node: ASTNode
    ) -> Binding:
        """型引数を保ったまま、Binding を指定 Right の参照へ変換する。"""
        match binding:
            case AtomicBinding(type=type_, policy=policy):
                return AtomicBinding(type_, right, policy, True)
            case AppliedBinding(atomic=AtomicBinding(type=type_, policy=policy), args=args):
                return AppliedBinding(
                    AtomicBinding(type_, right, policy, True), list(args)
                )
            case _:
                raise self.error_at(ErrorCode.CHECK_UNSUPPORTED_AST, node)

    def restrict_binding(
        self, binding: Binding, cap: Right, node: ASTNode
    ) -> Binding:
        """親 Place の権限を超えないよう、投影先 Binding を弱める。"""
        own = self.binding_right(binding, node)
        right = Right(
            AccessKind(min(own.access.value, cap.access.value)),
            (
                IdentityKind.UNIQUE
                if own.identity is cap.identity is IdentityKind.UNIQUE
                else IdentityKind.SHARED
            ),
        )
        if isinstance(binding, AtomicBinding):
            return AtomicBinding(binding.type, right, binding.policy, binding.is_ref)
        if isinstance(binding, AppliedBinding):
            atomic = binding.atomic
            return AppliedBinding(
                AtomicBinding(atomic.type, right, atomic.policy, atomic.is_ref),
                list(binding.args),
            )
        raise self.error_at(ErrorCode.CHECK_UNSUPPORTED_AST, node)

    def has_same_type(
        self, left: Binding, right: Binding, node: ASTNode
    ) -> bool:
        """二つの Binding の型と型引数が再帰的に同じか返す。"""
        match left, right:
            case AtomicBinding(type=left_type), AtomicBinding(type=right_type):
                return left_type == right_type
            case (
                AppliedBinding(atomic=AtomicBinding(type=left_type), args=left_args),
                AppliedBinding(atomic=AtomicBinding(type=right_type), args=right_args),
            ):
                return left_type == right_type and len(left_args) == len(right_args) and all(
                    self.has_same_type(left_arg, right_arg, node)
                    for left_arg, right_arg in zip(left_args, right_args)
                )
            case AtomicBinding() | AppliedBinding(), AtomicBinding() | AppliedBinding():
                return False
            case _:
                raise self.error_at(ErrorCode.CHECK_UNSUPPORTED_AST, node)

    def is_assignable(
        self, target: Binding, value: Binding, node: ASTNode
    ) -> bool:
        """value を target へ置けるかを、即値の一方向変換込みで判定する。

        型注釈・引数型・戻り値型が変換先を一意に与える場合だけ許す。
        変数の型推論や Binding 同士の比較では、この変換を使わない。
        """
        if self.has_same_type(target, value, node):
            return True
        match self.binding_type(target, node), self.binding_type(value, node):
            case IntType(), IntegerImmediateType():
                return True
            case FloatType(), DecimalImmediateType():
                return True
            case FloatType(), IntegerImmediateType():
                return True
            case _:
                return False

    def set_available_right(self, variable: Symbol, right: Right) -> None:
        """変数の現在の Right を設定する。"""
        self.right_state[variable] = Right(right.access, right.identity)

    def apply_right_split(
        self,
        host: Symbol,
        ref: Symbol,
        remaining: Right,
        borrowed: Right,
    ) -> None:
        """Host に残る Right と ref に貸し出す Right を記録する。"""
        self.set_available_right(host, remaining)
        self.set_available_right(ref, borrowed)

    def split_right(
        self, source: Right, rq: Right, node: ASTNode
    ) -> tuple[Right, Right]:
        """source を host 用と参照用の Right に分割する。"""
        if rq.access is AccessKind.NON or rq.access.value > source.access.value:
            raise self.error_at(ErrorCode.CHECK_INVALID_REFERENCE, node)
        if rq.identity is IdentityKind.UNIQUE:
            raise self.error_at(ErrorCode.CHECK_INVALID_REFERENCE, node)

        borrowed = Right(rq.access, rq.identity)
        if source.identity is IdentityKind.SHARED:
            return Right(source.access, IdentityKind.SHARED), borrowed
        if rq.access is AccessKind.WRITE:
            remaining_access = AccessKind.NON
        else:
            remaining_access = AccessKind.READ
        return Right(remaining_access, IdentityKind.SHARED), borrowed

    def require_movable_source(
        self, source: ExprResult, source_node: ASTNode, node: ASTNode
    ) -> None:
        """field/index を除く、move 元の共通条件を検査する。"""
        if isinstance(source_node, (_expr.MemberExpr, _expr.IndexExpr)):
            raise self.error_at(ErrorCode.CHECK_PARTIAL_MOVE_FORBIDDEN, source_node)
        if source.variable is None or self.is_reference(source.binding, source_node):
            raise self.error_at(ErrorCode.CHECK_INVALID_MOVE, node)
        self.require_result_right(
            source, Right(AccessKind.READ, IdentityKind.UNIQUE), source_node
        )

    def borrow_reference(
        self,
        source: ExprResult,
        target_binding: Binding,
        rq: Right,
        source_node: ASTNode,
        node: ASTNode,
    ) -> tuple[Binding, Right, Right, Right]:
        """単純変数の Right を ref 用に分割する共通処理。"""
        if isinstance(source_node, (_expr.MemberExpr, _expr.IndexExpr)):
            raise self.error_at(ErrorCode.CHECK_PARTIAL_REFERENCE_FORBIDDEN, source_node)
        if source.variable is None or self.is_reference(source.binding, source_node):
            raise self.error_at(ErrorCode.CHECK_INVALID_REFERENCE, node)
        self.require_result_right(source, rq, source_node)
        source_right = self.available_right(
            source.variable, source.binding, source_node
        )
        remaining, borrowed = self.split_right(source_right, rq, node)
        return (
            self.as_reference(target_binding, borrowed, node),
            remaining,
            borrowed,
            source_right,
        )

    def require_reference_target(
        self, target: ExprResult, source: ExprResult, node: ASTNode
    ) -> Symbol:
        """ref 先が ref 型で、貸与元より短命であることを検査する。"""
        if target.root is None or source.variable is None:
            raise self.error_at(ErrorCode.CHECK_INVALID_REFERENCE, node)
        if target.root == source.variable:
            raise self.error_at(ErrorCode.CHECK_INVALID_REFERENCE, node)
        if not self.is_reference(target.binding, node):
            raise self.error_at(ErrorCode.CHECK_REFERENCE_TARGET_NOT_REFERENCE, node)
        if target.root in self.active_reference_roots:
            raise self.error_at(
                ErrorCode.CHECK_REFERENCE_TARGET_ALREADY_ACTIVE, node
            )

        target_depth = self.context.general.scope_depth.get(target.root)
        source_depth = self.context.general.scope_depth.get(source.variable)
        if target_depth is None or source_depth is None:
            raise self.error_at(ErrorCode.CHECK_UNKNOWN_SYMBOL, node)
        if target_depth < source_depth:
            raise self.error_at(
                ErrorCode.CHECK_REFERENCE_TARGET_OUTLIVES_SOURCE, node
            )
        return target.root

    def restore_right(
        self,
        host: Symbol,
        target_root: Symbol,
        ref: Symbol | None,
        restored: Right,
    ) -> None:
        """ref を終了し、Right と root 単位の二重 ref 状態を戻す。"""
        self.set_available_right(host, restored)
        if ref is not None:
            self.right_state.pop(ref, None)
        self.active_reference_roots.discard(target_root)

    def require_right(
        self, variable: Symbol, binding: Binding, required: Right, node: ASTNode
    ) -> None:
        """現在の Right が必要な Right を満たさなければエラーにする。"""
        available = self.available_right(variable, binding, node)
        self.require_available_right(available, required, node)

    def require_result_right(
        self, result: ExprResult, required: Right, node: ASTNode
    ) -> None:
        """式結果が必要な Right を満たさなければエラーにする。"""
        match result:
            case ExprResult(variable=Symbol() as variable, binding=binding):
                self.require_right(variable, binding, required, node)
            case ExprResult(binding=binding):
                self.require_available_right(
                    self.binding_right(binding, node), required, node
                )

    def require_available_right(
        self, available: Right, required: Right, node: ASTNode
    ) -> None:
        """与えられた Right が必要な Right を満たすか検証する。"""
        allows_access = (
            required.access is AccessKind.NON
            or available.access is AccessKind.WRITE
            or available.access is required.access
        )
        allows_identity = (
            required.identity is IdentityKind.SHARED
            or available.identity is required.identity
        )
        if not allows_access or not allows_identity:
            raise self.error_at(ErrorCode.CHECK_RIGHT_VIOLATION, node)

    def visit_variable(self, expression: _expr.Variable) -> ExprResult:
        sym = self.context.general.sym.get(expression)
        if sym is None:
            raise self.error_at(ErrorCode.CHECK_UNKNOWN_SYMBOL, expression)
        binding = self.binding_of(sym, expression)
        effective = self.effective_binding(sym, binding, expression)
        if self.binding_right(effective, expression).access is AccessKind.NON:
            raise self.error_at(ErrorCode.CHECK_USE_AFTER_MOVE, expression)
        self.require_right(
            sym,
            effective,
            Right(AccessKind.READ, IdentityKind.SHARED),
            expression,
        )
        if isinstance(sym, symbol.FunctionSymbol):
            return ExprResult(effective)
        return ExprResult(effective, sym, sym)

    def visit_member_expression(self, expression: _expr.MemberExpr) -> ExprResult:
        """Class→Record または Record→field の投影を Place 経路として解決する。"""
        target = self.visit_expression(expression.expr)
        self.require_result_right(
            target,
            Right(AccessKind.READ, IdentityKind.SHARED),
            expression.expr,
        )

        target_type = self.binding_type(target.binding, expression.expr)
        if not isinstance(target_type, UserDefType):
            raise self.error_at(ErrorCode.CHECK_UNKNOWN_MEMBER, expression)

        class_ = self.context.general.classes.get(target_type.name)
        if class_ is not None:
            struct = self.context.general.structs_by_name.get(class_, {}).get(
                expression.name.name
            )
            record = (
                self.context.general.record_struct.get(struct)
                if struct is not None
                else None
            )
            if record is None:
                # Record field と同様に、Class ごとの名前表から def を直接解決する。
                definition = self.context.general.class_defs_by_name.get(
                    class_, {}
                ).get(expression.name.name)
                if definition is None:
                    fields = [
                        fields_by_name[expression.name.name]
                        for struct in self.context.general.struct_cls.get(class_, [])
                        if struct not in self.context.general.record_struct
                        for fields_by_name in [
                            self.context.general.struct_vars_by_name.get(struct, {})
                        ]
                        if expression.name.name in fields_by_name
                    ]
                    if len(fields) != 1:
                        raise self.error_at(ErrorCode.CHECK_UNKNOWN_MEMBER, expression)
                    binding = self.restrict_binding(
                        self.binding_of(fields[0], expression),
                        self.binding_right(target.binding, expression.expr),
                        expression,
                    )
                    return ExprResult(binding, root=target.root)
                return ExprResult(
                    self.binding_of(definition, expression), receiver=target
                )
            binding = AtomicBinding(
                UserDefType(record.name),
                self.binding_right(target.binding, expression.expr),
                NoPolicy(),
                self.is_reference(target.binding, expression.expr),
            )
            # field/index の状態は追跡しないが、寿命判定用に root だけ伝播する。
            return ExprResult(binding, root=target.root)

        record = self.context.general.records.get(target_type.name)
        if record is None:
            raise self.error_at(ErrorCode.CHECK_UNKNOWN_MEMBER, expression)
        field = self.context.general.record_vars_by_name.get(record, {}).get(
            expression.name.name
        )
        if field is None:
            raise self.error_at(ErrorCode.CHECK_UNKNOWN_MEMBER, expression)

        binding = self.restrict_binding(
            self.binding_of(field, expression),
            self.binding_right(target.binding, expression.expr),
            expression,
        )
        self.require_available_right(
            self.binding_right(binding, expression),
            Right(AccessKind.READ, IdentityKind.SHARED),
            expression,
        )
        return ExprResult(binding, root=target.root)

    def visit_call_expression(self, expression: _expr.CallExpr) -> ExprResult:
        """収集済み関数シグネチャを用いて、呼び出し引数と戻り値を検査する。"""
        callee = self.visit_expression(expression.callee)
        match callee.binding:
            case AppliedBinding(
                atomic=AtomicBinding(type=FunctionType()),
                args=[result, *parameters],
            ):
                pass
            case _:
                raise self.error_at(ErrorCode.CHECK_INVALID_ASSIGNMENT_TARGET, expression.callee)

        if callee.receiver is not None:
            if not parameters:
                raise self.error_at(ErrorCode.CHECK_MISSING_BINDING, expression.callee)
            # ``Taro.speak()`` の Taro は、def speak(me: Cat, ...) の
            # 明示された第1引数 ``me`` にだけ対応する。シグネチャ自体へ
            # 暗黙の receiver は挿入しない。
            receiver_parameter, *parameters = parameters
            self.require_result_right(
                callee.receiver,
                Right(AccessKind.READ, IdentityKind.SHARED),
                expression.callee,
            )
            if not self.has_same_type(
                callee.receiver.binding, receiver_parameter, expression.callee
            ):
                raise self.error_at(
                    ErrorCode.CHECK_FUNCTION_ARGUMENT_TYPE_MISMATCH,
                    expression.callee,
                )

        if len(expression.args) != len(parameters):
            raise self.error_at(
                ErrorCode.CHECK_FUNCTION_ARGUMENT_COUNT_MISMATCH, expression
            )
        for argument, parameter in zip(expression.args, parameters):
            value = self.visit_expression(argument)
            self.require_result_right(
                value,
                Right(AccessKind.READ, IdentityKind.SHARED),
                argument,
            )
            if not self.is_assignable(parameter, value.binding, argument):
                raise self.error_at(
                    ErrorCode.CHECK_FUNCTION_ARGUMENT_TYPE_MISMATCH, argument
                )
        return ExprResult(result)

    def visit_index_expression(self, expression: _expr.IndexExpr) -> ExprResult:
        """コンテナ要素の Binding を、親の Right で制限して返す。"""
        target = self.visit_expression(expression.expr)
        index = self.visit_expression(expression.index)
        self.require_result_right(
            target,
            Right(AccessKind.READ, IdentityKind.SHARED),
            expression.expr,
        )
        self.require_result_right(
            index,
            Right(AccessKind.READ, IdentityKind.SHARED),
            expression.index,
        )

        index_type = self.binding_type(index.binding, expression.index)
        if not isinstance(index_type, (IntegerImmediateType, IntType)):
            raise self.error_at(ErrorCode.CHECK_INDEX_NOT_INTEGER, expression.index)

        match target.binding:
            case AppliedBinding(
                atomic=AtomicBinding(type=(containerImmediateType() | ArrayType())),
                args=[element],
            ):
                element = self.restrict_binding(
                    element,
                    self.binding_right(target.binding, expression.expr),
                    expression,
                )
                return ExprResult(element, root=target.root)
            case _:
                raise self.error_at(ErrorCode.CHECK_INDEX_TARGET_NOT_INDEXABLE, expression.expr)

    def visit_arithmetic_expression(self, expression: _expr.ArithmeticExpr) -> ExprResult:
        # this
        right = self.visit_expression(expression.right).binding
        left = self.visit_expression(expression.left).binding
        if not isinstance(right, AtomicBinding):
            raise self.error_at(ErrorCode.CHECK_GENERIC_ARITHMETIC, expression.right)
        if not isinstance(left, AtomicBinding):
            raise self.error_at(ErrorCode.CHECK_GENERIC_ARITHMETIC, expression.left)
        if not left.right.access in (AccessKind.READ, AccessKind.WRITE):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.left)
        if not right.right.access in (AccessKind.READ, AccessKind.WRITE):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.right)
        if not isinstance(right.type, (DecimalImmediateType, IntegerImmediateType, IntType, FloatType)):
            raise self.error_at(ErrorCode.CHECK_ARITHMETIC_OPERAND_NOT_NUMERIC, expression.right)
        if not isinstance(left.type, (DecimalImmediateType, IntegerImmediateType, IntType, FloatType)):
            raise self.error_at(ErrorCode.CHECK_ARITHMETIC_OPERAND_NOT_NUMERIC, expression.left)

        if isinstance(left.type, (DecimalImmediateType, IntType)):
            is_float_left = False
        else:
            is_float_left = True
        if isinstance(right.type, (DecimalImmediateType, IntType)):
            is_float_right = False
        else:
            is_float_right = True

        if is_float_left and is_float_right:
            return ExprResult(AtomicBinding(
                DecimalImmediateType(),
                Right(AccessKind.READ, IdentityKind.UNIQUE),
                NoPolicy(),
                False,
            ))
        if is_float_left or is_float_right:
            return ExprResult(AtomicBinding(
                DecimalImmediateType(),
                Right(AccessKind.READ, IdentityKind.UNIQUE),
                NoPolicy(),
                False,
            ))
        return ExprResult(AtomicBinding(
            IntegerImmediateType(),
            Right(AccessKind.READ, IdentityKind.UNIQUE),
            NoPolicy(),
            False,
        ))

    def visit_logic_expression(self, expression: _expr.LogicExpr) -> ExprResult:
        right = self.visit_expression(expression.right).binding
        left = self.visit_expression(expression.left).binding
        if not isinstance(right, AtomicBinding):
            raise self.error_at(ErrorCode.CHECK_LOGIC_OPERAND_NOT_BOOLEAN, expression.right)
        if not isinstance(left, AtomicBinding):
            raise self.error_at(ErrorCode.CHECK_LOGIC_OPERAND_NOT_BOOLEAN, expression.left)
        if not isinstance(right.type, BoolType):
            raise self.error_at(ErrorCode.CHECK_LOGIC_OPERAND_NOT_BOOLEAN, expression.right)
        if not isinstance(left.type, BoolType):
            raise self.error_at(ErrorCode.CHECK_LOGIC_OPERAND_NOT_BOOLEAN, expression.left)
        if not left.right.access in (AccessKind.READ, AccessKind.WRITE):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.left)
        if not right.right.access in (AccessKind.READ, AccessKind.WRITE):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.right)
        return ExprResult(AtomicBinding(
            BoolType(),
            Right(AccessKind.READ, IdentityKind.UNIQUE),
            NoPolicy(),
            False,
        ))

    def visit_identity_expression(self, expression: _expr.IdentityExpr) -> ExprResult:
        right = self.visit_expression(expression.right).binding
        left = self.visit_expression(expression.left).binding
        if not isinstance(right, AtomicBinding):
            raise self.error_at(ErrorCode.CHECK_IDENTITY_OPERAND_GENERIC, expression.right)
        if not isinstance(left, AtomicBinding):
            raise self.error_at(ErrorCode.CHECK_IDENTITY_OPERAND_GENERIC, expression.left)

        if not left.right.access in (AccessKind.READ, AccessKind.WRITE):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.left)
        if not right.right.access in (AccessKind.READ, AccessKind.WRITE):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.right)

        if left.type != right.type:
            raise self.error_at(ErrorCode.CHECK_IDENTITY_OPERAND_TYPE_MISMATCH, expression)

        return ExprResult(AtomicBinding(
            BoolType(),
            Right(AccessKind.READ, IdentityKind.UNIQUE),
            NoPolicy(),
            False,
        ))

    def visit_comparison_expression(self, expression: _expr.CompExpr) -> ExprResult:
        right = self.visit_expression(expression.right).binding
        left = self.visit_expression(expression.left).binding
        if not isinstance(right, AtomicBinding):
            raise self.error_at(ErrorCode.CHECK_COMPARISON_OPERAND_GENERIC, expression.right)
        if not isinstance(left, AtomicBinding):
            raise self.error_at(ErrorCode.CHECK_COMPARISON_OPERAND_GENERIC, expression.left)

        if not left.right.access in (AccessKind.READ, AccessKind.WRITE):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.left)
        if not right.right.access in (AccessKind.READ, AccessKind.WRITE):
            raise self.error_at(ErrorCode.CHECK_CANT_READ, expression.right)
        if left.type != right.type:
            raise self.error_at(ErrorCode.CHECK_COMPARISON_OPERAND_TYPE_MISMATCH, expression)

        return ExprResult(AtomicBinding(
            BoolType(),
            Right(AccessKind.READ, IdentityKind.UNIQUE),
            NoPolicy(),
            False,
        ))

    def visit_assign_expression(self, expression: _expr.AssignExpr) -> ExprResult:
        """代入先の型と WRITE 権限を検査する。代入では Binding を変えない。"""
        left = self.visit_expression(expression.left)
        right = self.visit_expression(expression.right)

        if not isinstance(
            expression.left, (_expr.Variable, _expr.MemberExpr, _expr.IndexExpr)
        ):
            raise self.error_at(ErrorCode.CHECK_INVALID_ASSIGNMENT_TARGET, expression.left)

        if self.is_reference(left.binding, expression.left):
            raise self.error_at(ErrorCode.CHECK_INVALID_ASSIGNMENT_TARGET, expression.left)

        if self.binding_right(left.binding, expression.left).access is not AccessKind.WRITE:
            raise self.error_at(ErrorCode.CHECK_ASSIGN_TO_IMMUTABLE, expression.left)

        self.require_result_right(
            left,
            Right(AccessKind.WRITE, IdentityKind.SHARED),
            expression.left,
        )
        self.require_result_right(right, Right(AccessKind.READ, IdentityKind.SHARED), expression.right)


        if not self.is_assignable(left.binding, right.binding, expression):
            raise self.error_at(ErrorCode.CHECK_ASSIGNMENT_TYPE_MISMATCH, expression)

        return left

    def visit_move_expression(self, expression: _expr.MoveExpr) -> ExprResult:
        """変数どうしの move 元・先の型と排他権限を検査する。"""
        if isinstance(expression.left, (_expr.MemberExpr, _expr.IndexExpr)):
            raise self.error_at(ErrorCode.CHECK_PARTIAL_MOVE_FORBIDDEN, expression.left)
        left = self.visit_expression(expression.left)
        right = self.visit_expression(expression.right)

        if left.variable is None:
            raise self.error_at(ErrorCode.CHECK_INVALID_ASSIGNMENT_TARGET, expression.left)

        if self.is_reference(left.binding, expression.left):
            raise self.error_at(ErrorCode.CHECK_INVALID_ASSIGNMENT_TARGET, expression.left)

        self.require_result_right(
            left,
            Right(AccessKind.WRITE, IdentityKind.SHARED),
            expression.left,
        )
        self.require_movable_source(right, expression.right, expression)

        if not self.has_same_type(left.binding, right.binding, expression):
            raise self.error_at(ErrorCode.CHECK_ASSIGNMENT_TYPE_MISMATCH, expression)

        # field/index move は許さず、変数 root の所有権だけを移す。
        self.set_binding(left.variable, right.binding)
        self.set_available_right(
            right.variable, Right(AccessKind.NON, IdentityKind.SHARED)
        )
        self.move_edges.append((right.variable, left.variable))
        return left

    def visit_ref_expression(self, expression: _expr.RefExpr) -> ExprResult:
        """変数または field/index の ref 先へ、Right を一時貸与する。"""
        left = self.visit_expression(expression.left)
        right = self.visit_expression(expression.right)

        if not self.has_same_type(left.binding, right.binding, expression):
            raise self.error_at(ErrorCode.CHECK_ASSIGNMENT_TYPE_MISMATCH, expression)
        if expression.split_right is None:
            rq = Right(AccessKind.READ, IdentityKind.SHARED)
        else:
            rq = self.binding_right(expression.split_right, expression)

        reference_binding, remaining, borrowed, source = self.borrow_reference(
            right, left.binding, rq, expression.right, expression
        )

        assert right.variable is not None
        target_root = self.require_reference_target(left, right, expression)
        self.active_reference_roots.add(target_root)
        if left.variable is not None:
            self.set_binding(left.variable, reference_binding)
            self.apply_right_split(
                right.variable, left.variable, remaining, borrowed
            )
            ref = left.variable
        else:
            self.set_available_right(right.variable, remaining)
            ref = None
        self.loans[-1].append(Loan(right.variable, target_root, ref, source))

        return ExprResult(reference_binding, left.variable, left.root)

    def immediate_binding(self, type_: TypeDef) -> AtomicBinding:
        """即値が持つ読み取り専用の Binding を生成する。"""
        return AtomicBinding(
            type_,
            Right(AccessKind.READ, IdentityKind.UNIQUE),
            NoPolicy(),
            False,
        )

    def visit_container_immediate(self, expression: _expr.ContainerImmediate) -> ExprResult:
        elements = [self.visit_expression(value).binding for value in expression.value]
        if elements and any(
            not self.has_same_type(elements[0], element, expression)
            for element in elements[1:]
        ):
            raise self.error_at(ErrorCode.CHECK_CONTAINER_ELEMENT_TYPE_MISMATCH, expression)

        args: list[Binding] = []
        if elements:
            args.append(elements[0])
        return ExprResult(
            AppliedBinding(self.immediate_binding(containerImmediateType()), args)
        )

    def visit_string_immediate(self, expression: _expr.StringImmediate) -> ExprResult:
        return ExprResult(self.immediate_binding(StringImmediateType()))

    def visit_integer_immediate(self, expression: _expr.IntegerImmediate) -> ExprResult:
        return ExprResult(self.immediate_binding(IntegerImmediateType()))

    def visit_decimal_immediate(self, expression: _expr.DecimalImmediate) -> ExprResult:
        return ExprResult(self.immediate_binding(DecimalImmediateType()))

    def visit_none_immediate(self, expression: _expr.NoneImmediate) -> ExprResult:
        return ExprResult(self.immediate_binding(NoneType()))

    def visit_null_immediate(self, expression: _expr.NullImmediate) -> ExprResult:
        return ExprResult(self.immediate_binding(PtrType()))
