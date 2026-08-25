from __future__ import annotations

import difflib

import src.core.ast.base as _base
import src.core.ast.expr as _expr
import src.core.ast.stmt as _stmt
import src.core.contract.type.type as _t
import src.core.context.context as _ctx
from src.core.contract.contract import Contract
from src.core.contract.policy.policy import Policy, Policy_Generic, Policy_Union
from src.core.contract.right.right import (
    AccessKind, IdentityKind, RealRight, Right, Right_Generic, Right_Union,
)
from src.core.scope.scope import Scope
from src.core.source.source_span import SourceSpan
from src.core.symbol.symbol import FunctionSymbol, Symbol, VariableSymbol
from src.utils.error.base import KinakoBaseError, KinakoHelp, KinakoRelatedInfo
from src.utils.error.resolver import KinakoResolverError


class Resolver:
    def __init__(self, program: _stmt.ProgramStmt, source: str, context: _ctx.Context) -> None:
        self.program = program
        self.context = context
        self.source = source
        self.error: list[KinakoBaseError] = []
        self.scope = Scope(None, dict(context.symbols))
        self._function_declarations: dict[int, FunctionSymbol] = {}

    def resolve(self) -> None:
        """Resolve names in two passes so top-level functions may refer forward."""
        for statement in self.program.instr:
            if isinstance(statement, _stmt.FunctionDeclStmt):
                self._declare_function(statement)
        for statement in self.program.instr:
            self._visit_stmt(statement, top_level=True)

    def call_error(
        self,
        message: str,
        node: _base.ASTNode,
        related: list[KinakoRelatedInfo] | None = None,
        help: list[KinakoHelp] | None = None,
    ) -> KinakoResolverError:
        err = KinakoResolverError(
            message, node.line, node.col, self.source, node.len, related, help
        )
        self.error.append(err)
        return err

    def push_scope(self) -> None:
        self.scope = Scope(self.scope, {})

    def pop_scope(self, node: _base.ASTNode) -> None:
        if self.scope.parent is None:
            self.call_error(
                "コンパイラ内部エラー: ルートスコープをpopしようとしました。",
                node,
                help=[KinakoHelp("Resolverのスコープ処理を確認してください。")],
            )
            return
        self.scope = self.scope.parent

    @staticmethod
    def _span(node: _base.ASTNode) -> SourceSpan:
        return SourceSpan(node.line, node.col, node.len)

    def resolve_contract(self, contract: _base.Contract, err_node: _base.ASTNode) -> Contract:
        if contract.type is not None:
            contract.type_id = self.resolve_type_identifier(contract.type, err_node)
        if contract.right is not None:
            contract.right_id = self.resolve_right_identifier(contract.right, err_node)
        if contract.policy is not None:
            contract.policy_id = self.resolve_policy_identifier(contract.policy, err_node)
        return Contract(contract.type_id, contract.right_id, contract.policy_id)

    def resolve_type_identifier(
        self, identifier: _base.Identifier, err_node: _base.ASTNode
    ) -> _t.TypeDef | None:
        if isinstance(identifier, _base.Real_Identifier):
            resolved = self.context.buildin_type.get(identifier.name)
            if resolved is None:
                self.call_error(f"不明な型 `{identifier.name}` です。", err_node)
            return resolved

        if isinstance(identifier, _base.Union_Identifier):
            if not identifier.identifiers:
                self.call_error("空のUnion型は使用できません。", err_node)
                return None
            resolved = self.resolve_type_identifier(identifier.identifiers[0], err_node)
            for part in identifier.identifiers[1:]:
                other = self.resolve_type_identifier(part, err_node)
                if resolved is None or other is None:
                    resolved = None
                elif resolved != other:
                    resolved = self.context.intern_type(_t.UnionType(resolved, other))
            return resolved

        if isinstance(identifier, _base.Generic_Identifier):
            element = self.resolve_type_identifier(identifier.expr, err_node)
            generic = self.resolve_type_identifier(identifier.generic, err_node)
            if element is None or generic is None:
                return None
            if isinstance(generic, _t.ArrayType):
                return self.context.intern_type(_t.ArrayType(element, generic.size))
            if isinstance(generic, _t.PtrType):
                return self.context.intern_type(_t.PtrType(element))
            self.call_error("この型はジェネリック型として使用できません。", err_node)
            return None

        self.call_error("解決できない型識別子です。", err_node)
        return None

    def resolve_right_identifier(
        self, identifier: _base.Identifier, err_node: _base.ASTNode
    ) -> Right | None:
        if isinstance(identifier, _base.Real_Identifier):
            resolved = self.context.right.get(identifier.name)
            if resolved is None:
                self.call_error(f"不明なRight `{identifier.name}` です。", err_node)
            return resolved
        if isinstance(identifier, _base.Union_Identifier):
            if not identifier.identifiers:
                self.call_error("空のRight Unionは使用できません。", err_node)
                return None
            resolved = self.resolve_right_identifier(identifier.identifiers[0], err_node)
            for part in identifier.identifiers[1:]:
                other = self.resolve_right_identifier(part, err_node)
                resolved = None if resolved is None or other is None else Right_Union(resolved, other)
            return resolved
        if isinstance(identifier, _base.Generic_Identifier):
            generic = self.resolve_right_identifier(identifier.generic, err_node)
            element = self.resolve_right_identifier(identifier.expr, err_node)
            if generic is None or element is None:
                return None
            return Right_Generic(generic, element)
        self.call_error("解決できないRight識別子です。", err_node)
        return None

    def resolve_policy_identifier(
        self, identifier: _base.Identifier, err_node: _base.ASTNode
    ) -> Policy | None:
        if isinstance(identifier, _base.Real_Identifier):
            resolved = self.context.policy.get(identifier.name)
            if resolved is None:
                self.call_error(f"不明なPolicy `{identifier.name}` です。", err_node)
            return resolved
        if isinstance(identifier, _base.Union_Identifier):
            if not identifier.identifiers:
                self.call_error("空のPolicy Unionは使用できません。", err_node)
                return None
            resolved = self.resolve_policy_identifier(identifier.identifiers[0], err_node)
            for part in identifier.identifiers[1:]:
                other = self.resolve_policy_identifier(part, err_node)
                resolved = None if resolved is None or other is None else Policy_Union(resolved, other)
            return resolved
        if isinstance(identifier, _base.Generic_Identifier):
            generic = self.resolve_policy_identifier(identifier.generic, err_node)
            element = self.resolve_policy_identifier(identifier.expr, err_node)
            if generic is None or element is None:
                return None
            return Policy_Generic(generic, element)
        self.call_error("解決できないPolicy識別子です。", err_node)
        return None

    def get_names(self, name: str, count: int = 1) -> list[str]:
        names = list(self.context.policy)
        names += list(self.context.right)
        names += list(self.context.buildin_type)
        names += self.scope.names()
        return difflib.get_close_matches(name, names, count)

    def _declare_function(self, node: _stmt.FunctionDeclStmt) -> None:
        name = node.name.ident
        previous = self.scope.symbols.get(name)
        if previous is not None:
            self._duplicate_error(node, previous)
            return

        result = self.resolve_contract(node.result, node)
        parameters: list[VariableSymbol] = []
        parameter_names: set[str] = set()
        for parameter in node.params:
            parameter_contract = self.resolve_contract(parameter.contract, node)
            if parameter.name in parameter_names:
                self.call_error(f"仮引数 `{parameter.name}` が重複しています。", node)
                continue
            parameter_names.add(parameter.name)
            symbol = VariableSymbol(parameter.name, self._span(node), parameter_contract)
            parameter.symbol = symbol
            parameters.append(symbol)

        symbol = FunctionSymbol(name, self._span(node), result, parameters, node)
        node.symbol = symbol
        node.name.symbol = symbol
        self.scope.define(symbol)
        self.context.define(symbol)
        self._function_declarations[id(node)] = symbol

    def _declare_variable(
        self, node: _stmt.VariableDeclStmt, *, top_level: bool = False
    ) -> VariableSymbol | None:
        name = node.name.ident
        previous = self.scope.symbols.get(name)
        if previous is not None:
            self._duplicate_error(node, previous)
            return None

        contract = self.resolve_contract(node.contract, node)
        if contract.right is None:
            contract.right = RealRight(AccessKind.READ, IdentityKind.UNIQUE)
            node.contract.right_id = contract.right
        symbol = VariableSymbol(name, self._span(node), contract)
        node.symbol = symbol
        node.name.symbol = symbol
        self.scope.define(symbol)
        if top_level:
            self.context.define(symbol)
        return symbol

    def _duplicate_error(self, node: _base.ASTNode, previous: Symbol) -> None:
        span = previous.span
        self.call_error(
            f"宣言 `{previous.name}` が重複しています。",
            node,
            related=[KinakoRelatedInfo("先に宣言されています。", span.line, span.col, span.len)],
        )

    def _visit_stmt(self, node: _stmt.Stmt, *, top_level: bool = False) -> None:
        if isinstance(node, _stmt.VariableDeclStmt):
            if node.left is not None:
                self._visit_expr(node.left)
            self._declare_variable(node, top_level=top_level)
            return

        if isinstance(node, _stmt.FunctionDeclStmt):
            symbol = self._function_declarations.get(id(node))
            if symbol is None:
                return
            self.push_scope()
            for parameter in symbol.parameters:
                self.scope.define(parameter)
            self._visit_stmt(node.body)
            self.pop_scope(node)
            return

        if isinstance(node, _stmt.BlockStmt):
            self.push_scope()
            for statement in node.instr:
                self._visit_stmt(statement)
            self.pop_scope(node)
            return

        if isinstance(node, _stmt.Ifstmt):
            self._visit_expr(node.cond)
            self._visit_scoped_stmt(node.then_stmt)
            if node.else_stmt is not None:
                self._visit_scoped_stmt(node.else_stmt)
            return

        if isinstance(node, _stmt.WhileStmt):
            self._visit_expr(node.cond)
            self._visit_scoped_stmt(node.loop)
            return

        if isinstance(node, _stmt.ForEachStmt):
            self._visit_expr(node.iterator)
            self.push_scope()
            loop_contract = self.resolve_contract(node.contract, node)
            if loop_contract.right is None:
                loop_contract.right = RealRight(AccessKind.READ, IdentityKind.UNIQUE)
                node.contract.right_id = loop_contract.right
            symbol = VariableSymbol(node.variable.ident, self._span(node.variable), loop_contract)
            node.variable.symbol = symbol
            self.scope.define(symbol)
            self._visit_stmt(node.loop)
            self.pop_scope(node)
            return

        for child in node.get_child():
            if isinstance(child, _expr.Expr):
                self._visit_expr(child)
            elif isinstance(child, _stmt.Stmt):
                self._visit_stmt(child)

    def _visit_scoped_stmt(self, node: _stmt.Stmt) -> None:
        self.push_scope()
        self._visit_stmt(node)
        self.pop_scope(node)

    def _visit_expr(self, node: _expr.Expr) -> None:
        if isinstance(node, _expr.Variable):
            symbol = self.scope.lookup(node.ident)
            if symbol is not None:
                node.symbol = symbol
                return

            suggestions = self.get_names(node.ident)
            if suggestions:
                suggested = self.scope.lookup(suggestions[0])
                related = None
                if suggested is not None:
                    span = suggested.span
                    related = [KinakoRelatedInfo(
                        f"もしかしたら `{suggestions[0]}` ですか？",
                        span.line, span.col, span.len,
                    )]
                self.call_error(
                    f"不明な名前 `{node.ident}` です。",
                    node,
                    related=related,
                    help=None if suggested is not None else [
                        KinakoHelp(f"もしかしたら `{suggestions[0]}` ですか？")
                    ],
                )
                return

            visible = ", ".join(self.scope.names()) or "なし"
            self.call_error(
                f"不明な名前 `{node.ident}` です。",
                node,
                help=[KinakoHelp(f"現在参照できる名前: {visible}")],
            )
            return

        if isinstance(node, _expr.MemberExpr):
            # Member lookup needs the receiver type and is therefore handled
            # by the checker against ClassSymbol.members.
            self._visit_expr(node.expr)
            return

        for child in node.get_child():
            if isinstance(child, _expr.Expr):
                self._visit_expr(child)
