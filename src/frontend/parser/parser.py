"""Parser for the current Kinako AST."""
from __future__ import annotations

from collections.abc import Callable

from src.core.token.token import Token
from src.core.token.tokentype import TokenType
from src.core.ast import base as _base
from src.core.ast import expr as _expr
from src.core.ast import stmt as _stmt
from src.utils.error.code import ErrorCode
from src.utils.error.syntax import KinakoSyntaxError

ExpressionParser = Callable[[], _expr.Expr]
BinaryFactory = Callable[[Token, _expr.Expr, _expr.Expr], _expr.Expr]


class Parser:
    def __init__(self, tokens: list[Token], source: str) -> None:
        self.tokens, self.source, self.pos = tokens, source, 0
        self.error: list[KinakoSyntaxError] = []

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def previous(self) -> Token:
        return self.tokens[max(0, self.pos - 1)]

    def is_at_end(self) -> bool:
        return self.peek().type is TokenType.EOF

    def advance(self) -> Token:
        token = self.peek()
        if not self.is_at_end():
            self.pos += 1
        return token

    def check(self, kind: TokenType) -> bool:
        return self.peek().type is kind

    def match(self, *kinds: TokenType) -> bool:
        if self.peek().type in kinds:
            self.advance()
            return True
        return False

    def error_at(
        self, token: Token, code: ErrorCode, message: str | None = None
    ) -> KinakoSyntaxError:
        rendered_message = f"[{code.code}] {code.message}"
        if message is not None:
            rendered_message = f"{rendered_message}: {message}"
        error = KinakoSyntaxError(
            rendered_message, token.line, token.column, self.source, token.len
        )
        self.error.append(error)
        return error

    def consume(self, kind: TokenType) -> Token:
        if self.check(kind):
            return self.advance()
        codes = {
            TokenType.ID: ErrorCode.SYNTAX_EXPECTED_IDENTIFIER,
            TokenType.SEMI: ErrorCode.SYNTAX_EXPECTED_SEMICOLON,
            TokenType.LPAREN: ErrorCode.SYNTAX_EXPECTED_OPEN_PAREN,
            TokenType.RPAREN: ErrorCode.SYNTAX_EXPECTED_CLOSE_PAREN,
            TokenType.LBRACE: ErrorCode.SYNTAX_EXPECTED_OPEN_BRACE,
            TokenType.RBRACE: ErrorCode.SYNTAX_EXPECTED_CLOSE_BRACE,
            TokenType.RBRACKET: ErrorCode.SYNTAX_EXPECTED_CLOSE_BRACKET,
            TokenType.COLON: ErrorCode.SYNTAX_EXPECTED_COLON,
            TokenType.ARROW: ErrorCode.SYNTAX_EXPECTED_ARROW,
            TokenType.RQ: ErrorCode.SYNTAX_EXPECTED_INTERFACE_REQUEST,
            TokenType.FN: ErrorCode.SYNTAX_EXPECTED_FUNCTION,
            TokenType.DEF: ErrorCode.SYNTAX_EXPECTED_DEFINITION,
        }
        code = codes.get(kind, ErrorCode.SYNTAX_EXPECTED_TOKEN)
        raise self.error_at(self.peek(), code, kind.name)

    def identifier(self) -> _base.Identifier:
        token = self.consume(TokenType.ID)
        return _base.Identifier(token.value)

    def type_identifier(self) -> _base.Identifier:
        if self.peek().type in (TokenType.ID, TokenType.NONE):
            token = self.advance()
            return _base.Identifier(token.value)
        raise self.error_at(self.peek(), ErrorCode.SYNTAX_EXPECTED_TYPE)

    def parse(self) -> _stmt.Program:
        result: list[_stmt.Stmt] = []
        while not self.is_at_end():
            result.append(self.statement())
        return _stmt.Program(1, 1, 0, result)

    # Statements
    def statement(self) -> _stmt.Stmt:
        match self.peek().type:
            case TokenType.LET:
                return self.let_statement()
            case TokenType.UNSAFE:
                return self.unsafe_statement()
            case TokenType.IMPORT:
                return self.import_statement()
            case TokenType.VAR:
                raise self.error_at(
                    self.peek(), ErrorCode.SYNTAX_UNSUPPORTED_STATEMENT, "VAR"
                )
            case TokenType.WHILE:
                return self.while_statement()
            case TokenType.IF:
                return self.if_statement()
            case TokenType.RETURN:
                return self.return_statement()
            case TokenType.ASM:
                return self.asm_statement()
            case TokenType.FOR:
                raise self.error_at(self.peek(), ErrorCode.SYNTAX_UNSUPPORTED_STATEMENT, "FOR")
            case TokenType.RECORD:
                return self.record_declaration()
            case TokenType.INTERFACE:
                return self.interface_declaration()
            case TokenType.CLASS:
                return self.class_declaration()
            case TokenType.FN:
                return self.function_declaration()
            case TokenType.LBRACE:
                return self.block()
            case _:
                result = self.expression()
                self.consume(TokenType.SEMI)
                return _stmt.ExprStmt(
                    result.line,
                    result.col,
                    result.len,
                    result,
                )

    def unsafe_statement(self) -> _stmt.UnsafeStmt:
        start = self.advance()
        match self.peek().type:
            case TokenType.LET:
                inner = self.let_statement()
            case TokenType.RETURN:
                inner = self.return_statement()
            case TokenType.ASM:
                inner = self.asm_statement()
            case TokenType.IMPORT | TokenType.IF | TokenType.WHILE | TokenType.FN | TokenType.CLASS | TokenType.RECORD | TokenType.INTERFACE | TokenType.LBRACE:
                raise self.error_at(self.peek(), ErrorCode.SYNTAX_UNSUPPORTED_STATEMENT, "unsafe requires a SimpleStmt")
            case _:
                expression = self.expression()
                self.consume(TokenType.SEMI)
                inner = _stmt.ExprStmt(expression.line, expression.col, expression.len, expression)
        return _stmt.UnsafeStmt(start.line, start.column, start.len, inner)

    def let_statement(self) -> _stmt.LocalStmt:
        start = self.advance()
        left = self.identifier()
        contract: _base.TypeNode | None = None
        if self.match(TokenType.COLON):
            if self.match(TokenType.MOVE):
                right = self.expression()
                self.consume(TokenType.SEMI)
                return _stmt.MoveStmt(start.line, start.column, start.len, left, right, None)
            contract = self.type_node()
        if self.match(TokenType.REF):
            right = self.expression()
            self.consume(TokenType.SEMI)
            return _stmt.RefStmt(start.line, start.column, start.len, left, right, contract)
        if self.match(TokenType.MOVE):
            right = self.expression()
            self.consume(TokenType.SEMI)
            return _stmt.MoveStmt(start.line, start.column, start.len, left, right, contract)
        right = self.expression() if self.match(TokenType.ASSIGN) else None
        self.consume(TokenType.SEMI)
        return _stmt.LetStmt(start.line, start.column, start.len, left, right, contract)  # type: ignore[arg-type]

    def import_statement(self) -> _stmt.ImportStmt:
        start = self.advance()
        path = [self.identifier()]
        while self.match(TokenType.DOT):
            path.append(self.identifier())
        self.consume(TokenType.SEMI)
        return _stmt.ImportStmt(start.line, start.column, start.len, path)

    def var_statement(self) -> _stmt.VarDeclStmt:
        start = self.advance()
        name = self.identifier()
        typ = self.type_node() if self.match(TokenType.COLON) else None
        self.consume(TokenType.SEMI)
        return _stmt.VarDeclStmt(start.line, start.column, start.len, name, typ)

    def block(self) -> _stmt.Block:
        start = self.consume(TokenType.LBRACE)
        result: list[_stmt.Stmt] = []
        while not self.check(TokenType.RBRACE):
            if self.is_at_end():
                raise self.error_at(self.peek(), ErrorCode.SYNTAX_UNCLOSED_BLOCK)
            result.append(self.statement())
        self.advance()
        return _stmt.Block(start.line, start.column, start.len, result)

    def if_statement(self) -> _stmt.IfStmt:
        start = self.advance()
        condition = self.expression()
        then = self.block()
        other: _stmt.Stmt | None = None
        if self.match(TokenType.ELIF):
            other = self.if_statement_from_elif(self.previous())
        elif self.match(TokenType.ELSE):
            other = self.if_statement() if self.check(TokenType.IF) else self.block()
        return _stmt.IfStmt(start.line, start.column, start.len, then, other, condition)

    def if_statement_from_elif(self, start: Token) -> _stmt.IfStmt:
        condition = self.expression(); then = self.block(); other = None
        if self.match(TokenType.ELIF): other = self.if_statement_from_elif(self.previous())
        elif self.match(TokenType.ELSE): other = self.if_statement() if self.check(TokenType.IF) else self.block()
        return _stmt.IfStmt(start.line, start.column, start.len, then, other, condition)

    def while_statement(self) -> _stmt.WhileStmt:
        start = self.advance(); condition = self.expression(); body = self.block()
        return _stmt.WhileStmt(start.line, start.column, start.len, body, condition)

    def return_statement(self) -> _stmt.ReturnStmt:
        start = self.advance(); value = self.expression()
        self.consume(TokenType.SEMI)
        return _stmt.ReturnStmt(start.line, start.column, start.len, value)

    def asm_statement(self) -> _stmt.AsmStmt:
        start = self.advance()
        self.consume(TokenType.LPAREN)
        template = self.consume(TokenType.STRING)
        self.consume(TokenType.RPAREN)
        self.consume(TokenType.SEMI)
        value = bytes(template.value[1:-1], "utf-8").decode("unicode_escape")
        return _stmt.AsmStmt(start.line, start.column, start.len, value)

    # Declarations
    def function_header(
        self, token_type: TokenType
    ) -> tuple[Token, _base.Identifier, list[_stmt.Parameter], _base.TypeNode]:
        start = self.consume(token_type); name = self.identifier()
        self.consume(TokenType.LPAREN); parms: list[_stmt.Parameter] = []
        if not self.check(TokenType.RPAREN):
            while True:
                token = self.consume(TokenType.ID); self.consume(TokenType.COLON)
                parms.append(_stmt.Parameter(token.line, token.column, token.len, _base.Identifier(token.value), self.type_node()))
                if not self.match(TokenType.COMMA): break
        self.consume(TokenType.RPAREN); self.consume(TokenType.ARROW)
        return start, name, parms, self.type_node()

    def function_declaration(self) -> _stmt.FunctionStmt:
        start, name, parms, result = self.function_header(TokenType.FN)
        return _stmt.FunctionStmt(start.line, start.column, start.len, name, parms, result, self.block())
    def function_definition(self) -> _stmt.FunctionDefStmt:
        start, name, parms, result = self.function_header(TokenType.DEF)
        return _stmt.FunctionDefStmt(start.line, start.column, start.len, name, parms, result, self.block())

    def record_declaration(self) -> _stmt.RecordDeclStmt:
        start = self.advance(); name = self.identifier(); self.consume(TokenType.LBRACE)
        members: list[_stmt.DeclStmt] = []
        while not self.check(TokenType.RBRACE):
            if not self.check(TokenType.VAR):
                raise self.error_at(self.peek(), ErrorCode.SYNTAX_INVALID_RECORD_MEMBER)
            members.append(self.var_statement())
        self.advance(); return _stmt.RecordDeclStmt(start.line, start.column, start.len, name, members)

    def interface_declaration(self) -> _stmt.InterfaceDeclStmt:
        start = self.advance(); name = self.identifier(); self.consume(TokenType.LBRACE)
        members: list[_stmt.FunctionRequestStmt] = []
        while not self.check(TokenType.RBRACE):
            rq = self.consume(TokenType.RQ); fn = self.identifier()
            self.consume(TokenType.LPAREN); parms: list[_stmt.Parameter] = []
            if not self.check(TokenType.RPAREN):
                while True:
                    token = self.consume(TokenType.ID); self.consume(TokenType.COLON)
                    parms.append(_stmt.Parameter(token.line, token.column, token.len, _base.Identifier(token.value), self.type_node()))
                    if not self.match(TokenType.COMMA): break
            self.consume(TokenType.RPAREN); self.consume(TokenType.ARROW)
            result = self.type_node(); self.consume(TokenType.SEMI)
            members.append(_stmt.FunctionRequestStmt(rq.line, rq.column, rq.len, fn, parms, result))
        self.advance(); return _stmt.InterfaceDeclStmt(start.line, start.column, start.len, name, members)

    def class_declaration(self) -> _stmt.ClassDeclStmt:
        start = self.advance(); name = self.identifier(); self.consume(TokenType.LBRACE)
        members: list[_stmt.ClassMemberStmt] = []
        while not self.check(TokenType.RBRACE):
            if self.match(TokenType.STRUCT):
                token = self.previous()
                if self.match(TokenType.USE):
                    target = self.identifier(); self.consume(TokenType.SEMI)
                    members.append(_stmt.StructUseStmt(token.line, token.column, token.len, target))
                else: members.append(self.struct_declaration(token))
            elif self.match(TokenType.IMPL): members.append(self.impl_declaration(self.previous()))
            else: raise self.error_at(self.peek(), ErrorCode.SYNTAX_INVALID_CLASS_MEMBER)
        self.advance(); return _stmt.ClassDeclStmt(start.line, start.column, start.len, name, members)

    def struct_declaration(self, start: Token) -> _stmt.StructDeclStmt:
        self.consume(TokenType.LBRACE); members: list[_stmt.VarDeclStmt] = []
        while not self.check(TokenType.RBRACE):
            if not self.check(TokenType.VAR): raise self.error_at(self.peek(), ErrorCode.SYNTAX_INVALID_STRUCT_MEMBER)
            members.append(self.var_statement())
        self.advance(); return _stmt.StructDeclStmt(start.line, start.column, start.len, members)

    def impl_declaration(self, start: Token) -> _stmt.ClassMemberStmt:
        interface = self.identifier() if self.match(TokenType.USE) else None
        self.consume(TokenType.LBRACE); members: list[_stmt.FunctionDefStmt] = []
        while not self.check(TokenType.RBRACE):
            if not self.check(TokenType.DEF): raise self.error_at(self.peek(), ErrorCode.SYNTAX_INVALID_IMPL_MEMBER)
            members.append(self.function_definition())
        self.advance()
        return _stmt.ImplUseStmt(start.line, start.column, start.len, interface, members) if interface else _stmt.ImplStmt(start.line, start.column, start.len, members)

    # Types
    def bindings(self) -> list[_base.Binding]:
        result: list[_base.Binding] = []
        while self.match(TokenType.AT): result.append(_base.Binding(self.identifier()))
        return result
    def type_node(self) -> _base.TypeNode:
        is_ref = self.match(TokenType.REF)
        base_name = self.type_identifier()
        if not self.match(TokenType.LBRACKET):
            return _base.Name(_base.TypeSyn(is_ref, base_name, self.bindings()))
        args: list[_base.TypeSyn] = []
        while not self.check(TokenType.RBRACKET):
            is_ref = self.match(TokenType.REF); arg = self.type_identifier()
            args.append(_base.TypeSyn(is_ref, arg, self.bindings()))
            if not self.match(TokenType.COMMA): break
        self.consume(TokenType.RBRACKET)
        base = _base.Name(_base.TypeSyn(is_ref, base_name, self.bindings()))
        return _base.Container(base, args)

    # Expressions
    def expression(self) -> _expr.Expr:
        return self.assignment()

    def assignment(self) -> _expr.Expr:
        left = self.logic_or()
        if self.match(TokenType.ASSIGN):
            token = self.previous(); return _expr.AssignExpr(token.line, token.column, token.len, self.assignment(), left)
        if self.match(TokenType.PLUS_ASSIGN):
            token = self.previous(); right = self.assignment()
            return _expr.AssignExpr(token.line, token.column, token.len, _expr.ArithmeticExpr(token.line, token.column, token.len, _expr.ArithmeticKind.ADD, left, right), left)
        if self.match(TokenType.REF):
            token = self.previous()
            return _expr.RefExpr(
                token.line, token.column, token.len, self.assignment(), left, None
            )
        return left
    def binary(
        self,
        next_method: ExpressionParser,
        kinds: set[TokenType],
        factory: BinaryFactory,
    ) -> _expr.Expr:
        left = next_method()
        while self.peek().type in kinds:
            token = self.advance(); left = factory(token, left, next_method())
        return left
    def logic_or(self) -> _expr.Expr:
        return self.binary(self.logic_and, {TokenType.LOGIC_OR}, lambda t, l, r: _expr.LogicExpr(t.line, t.column, t.len, _expr.LogicKind.OR, l, r))  # type: ignore[arg-type]

    def logic_and(self) -> _expr.Expr:
        return self.binary(self.identity, {TokenType.LOGIC_AND}, lambda t, l, r: _expr.LogicExpr(t.line, t.column, t.len, _expr.LogicKind.AND, l, r))  # type: ignore[arg-type]

    def identity(self) -> _expr.Expr:
        kinds={TokenType.EQ:_expr.IdentityKind.EQ,TokenType.NE:_expr.IdentityKind.NE}
        return self.binary(self.comparison,set(kinds),lambda t,l,r:_expr.IdentityExpr(t.line,t.column,t.len,kinds[t.type],l,r))
    def comparison(self) -> _expr.Expr:
        kinds={TokenType.LABRACKET:_expr.CompKind.LT,TokenType.RABRACKET:_expr.CompKind.GT,TokenType.LE:_expr.CompKind.LE,TokenType.GE:_expr.CompKind.GE}
        return self.binary(self.term,set(kinds),lambda t,l,r:_expr.CompExpr(t.line,t.column,t.len,kinds[t.type],l,r))
    def term(self) -> _expr.Expr:
        kinds={TokenType.PLUS:_expr.ArithmeticKind.ADD,TokenType.MINUS:_expr.ArithmeticKind.SUB}
        return self.binary(self.factor,set(kinds),lambda t,l,r:_expr.ArithmeticExpr(t.line,t.column,t.len,kinds[t.type],l,r))
    def factor(self) -> _expr.Expr:
        kinds={TokenType.MULT:_expr.ArithmeticKind.MUL,TokenType.DIV:_expr.ArithmeticKind.DIV,TokenType.MOD:_expr.ArithmeticKind.MOD}
        return self.binary(self.postfix,set(kinds),lambda t,l,r:_expr.ArithmeticExpr(t.line,t.column,t.len,kinds[t.type],l,r))
    def postfix(self) -> _expr.Expr:
        value=self.primary()
        while True:
            if self.match(TokenType.LBRACKET):
                index=self.expression(); end=self.consume(TokenType.RBRACKET)
                value=_expr.IndexExpr(end.line,end.column,end.len,value,index)
            elif self.match(TokenType.DOT):
                name=self.identifier(); token=self.previous()
                value=_expr.MemberExpr(token.line,token.column,token.len,value,name)
            elif self.match(TokenType.LPAREN):
                # 後置式の直後に括弧を許すため、`obj.method()` も同じ経路で構文解析する。
                args: list[_expr.Expr] = []
                if not self.check(TokenType.RPAREN):
                    while True:
                        args.append(self.expression())
                        if not self.match(TokenType.COMMA):
                            break
                end = self.consume(TokenType.RPAREN)
                value = _expr.CallExpr(end.line, end.column, end.len, value, args)
            else: return value
    def primary(self) -> _expr.Expr:
        token=self.advance()
        if token.type is TokenType.LBRACKET:
            # 空配列と任意個の式からなるコンテナ即値をここで構文解析する。
            values: list[_expr.Expr] = []
            if not self.check(TokenType.RBRACKET):
                while True:
                    values.append(self.expression())
                    if not self.match(TokenType.COMMA):
                        break
            self.consume(TokenType.RBRACKET)
            return _expr.ContainerImmediate(
                token.line, token.column, token.len, values
            )
        if token.type is TokenType.NUMBER: return _expr.IntegerImmediate(token.line,token.column,token.len,int(token.value))
        if token.type is TokenType.DECIMAL: return _expr.DecimalImmediate(token.line,token.column,token.len,float(token.value))
        if token.type is TokenType.STRING: return _expr.StringImmediate(token.line,token.column,token.len,bytes(token.value[1:-1],"utf-8").decode("unicode_escape"))
        if token.type is TokenType.ID:
            name = _base.Identifier(token.value)
            return _expr.Variable(token.line, token.column, token.len, name)
        if token.type == TokenType.NONE:
            return _expr.NoneImmediate(token.line, token.column, token.len)
        if token.type == TokenType.NULL:
            return _expr.NullImmediate(token.line, token.column, token.len)
        if token.type is TokenType.LPAREN:
            value=self.expression(); self.consume(TokenType.RPAREN); return value
        raise self.error_at(token, ErrorCode.SYNTAX_INVALID_EXPRESSION, token.value)
