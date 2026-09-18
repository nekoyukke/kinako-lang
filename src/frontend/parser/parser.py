"""Parser for the current Kinako AST."""
from __future__ import annotations

from collections.abc import Callable

from src.core.token.token import Token
from src.core.token.tokentype import TokenType
from src.core.ast import base as _base
from src.core.ast import expr as _expr
from src.core.ast import stmt as _stmt
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

    def error_at(self, token: Token, message: str) -> KinakoSyntaxError:
        error = KinakoSyntaxError(
            message, token.line, token.column, self.source, token.len
        )
        self.error.append(error)
        return error

    def consume(self, kind: TokenType, message: str) -> Token:
        if self.check(kind):
            return self.advance()
        raise self.error_at(self.peek(), message)

    def identifier(self, message: str) -> _base.Identifier:
        token = self.consume(TokenType.ID, message)
        return _base.Identifier(token.value)
    def type_identifier(self, message: str) -> _base.Identifier:
        if self.peek().type in (TokenType.ID, TokenType.NONE):
            token = self.advance()
            return _base.Identifier(token.value)
        raise self.error_at(self.peek(), message)

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
            case TokenType.VAR:
                return self.var_statement()
            case TokenType.WHILE:
                return self.while_statement()
            case TokenType.IF:
                return self.if_statement()
            case TokenType.RETURN:
                return self.return_statement()
            case TokenType.FOR:
                raise self.error_at(self.peek(), "for は現在未実装です")
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
                self.consume(TokenType.SEMI, "文の末尾に ';' が必要です")
                return result  # type: ignore[return-value]

    def let_statement(self) -> _stmt.LocalStmt:
        start = self.advance()
        left = self.identifier("let の後に識別子が必要です")
        contract: _base.TypeNode | None = None
        if self.match(TokenType.COLON):
            if self.match(TokenType.MOVE):
                right = self.expression()
                self.consume(TokenType.SEMI, "move 文の末尾に ';' が必要です")
                return _stmt.MoveStmt(start.line, start.column, start.len, left, right, None)
            contract = self.type_node()
        if self.match(TokenType.REF):
            right = self.expression()
            self.consume(TokenType.SEMI, "ref 文の末尾に ';' が必要です")
            return _stmt.RefStmt(start.line, start.column, start.len, left, right, contract)
        if self.match(TokenType.MOVE):
            right = self.expression()
            self.consume(TokenType.SEMI, "move 文の末尾に ';' が必要です")
            return _stmt.MoveStmt(start.line, start.column, start.len, left, right, contract)
        right = self.expression() if self.match(TokenType.ASSIGN) else None
        self.consume(TokenType.SEMI, "let 文の末尾に ';' が必要です")
        return _stmt.LetStmt(start.line, start.column, start.len, left, right, contract)  # type: ignore[arg-type]

    def var_statement(self) -> _stmt.VarDeclStmt:
        start = self.advance()
        name = self.identifier("var の後に識別子が必要です")
        typ = self.type_node() if self.match(TokenType.COLON) else None
        self.consume(TokenType.SEMI, "var 文の末尾に ';' が必要です")
        return _stmt.VarDeclStmt(start.line, start.column, start.len, name, typ)

    def block(self) -> _stmt.Block:
        start = self.consume(TokenType.LBRACE, "'{' が必要です")
        result: list[_stmt.Stmt] = []
        while not self.check(TokenType.RBRACE):
            if self.is_at_end():
                raise self.error_at(self.peek(), "block が閉じられていません")
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
        self.consume(TokenType.SEMI, "return 文の末尾に ';' が必要です")
        return _stmt.ReturnStmt(start.line, start.column, start.len, value)

    # Declarations
    def function_header(
        self, token_type: TokenType
    ) -> tuple[Token, _base.Identifier, list[_stmt.Parameter], _base.TypeNode]:
        start = self.consume(token_type, "関数キーワードが必要です"); name = self.identifier("関数名が必要です")
        self.consume(TokenType.LPAREN, "関数名の後に '(' が必要です"); parms: list[_stmt.Parameter] = []
        if not self.check(TokenType.RPAREN):
            while True:
                token = self.consume(TokenType.ID, "引数名が必要です"); self.consume(TokenType.COLON, "引数名の後に ':' が必要です")
                parms.append(_stmt.Parameter(token.line, token.column, token.len, _base.Identifier(token.value), self.type_node()))
                if not self.match(TokenType.COMMA): break
        self.consume(TokenType.RPAREN, "引数リストを ')' で閉じてください"); self.consume(TokenType.ARROW, "戻り値型の前に '->' が必要です")
        return start, name, parms, self.type_node()

    def function_declaration(self) -> _stmt.FunctionStmt:
        start, name, parms, result = self.function_header(TokenType.FN)
        return _stmt.FunctionStmt(start.line, start.column, start.len, name, parms, result, self.block())
    def function_definition(self) -> _stmt.FunctionDefStmt:
        start, name, parms, result = self.function_header(TokenType.DEF)
        return _stmt.FunctionDefStmt(start.line, start.column, start.len, name, parms, result, self.block())

    def record_declaration(self) -> _stmt.RecordDeclStmt:
        start = self.advance(); name = self.identifier("record 名が必要です"); self.consume(TokenType.LBRACE, "record の本体に '{' が必要です")
        members: list[_stmt.DeclStmt] = []
        while not self.check(TokenType.RBRACE):
            if not self.check(TokenType.VAR): raise self.error_at(self.peek(), "record には var 宣言だけを書けます")
            members.append(self.var_statement())
        self.advance(); return _stmt.RecordDeclStmt(start.line, start.column, start.len, name, members)

    def interface_declaration(self) -> _stmt.InterfaceDeclStmt:
        start = self.advance(); name = self.identifier("interface 名が必要です"); self.consume(TokenType.LBRACE, "interface の本体に '{' が必要です")
        members: list[_stmt.FunctionRequestStmt] = []
        while not self.check(TokenType.RBRACE):
            rq = self.consume(TokenType.RQ, "interface には rq 宣言だけを書けます"); fn = self.identifier("要求関数名が必要です")
            self.consume(TokenType.LPAREN, "関数名の後に '(' が必要です"); parms: list[_stmt.Parameter] = []
            if not self.check(TokenType.RPAREN):
                while True:
                    token = self.consume(TokenType.ID, "引数名が必要です"); self.consume(TokenType.COLON, "引数名の後に ':' が必要です")
                    parms.append(_stmt.Parameter(token.line, token.column, token.len, _base.Identifier(token.value), self.type_node()))
                    if not self.match(TokenType.COMMA): break
            self.consume(TokenType.RPAREN, "引数リストを ')' で閉じてください"); self.consume(TokenType.ARROW, "戻り値型の前に '->' が必要です")
            result = self.type_node(); self.consume(TokenType.SEMI, "rq 宣言の末尾に ';' が必要です")
            members.append(_stmt.FunctionRequestStmt(rq.line, rq.column, rq.len, fn, parms, result))
        self.advance(); return _stmt.InterfaceDeclStmt(start.line, start.column, start.len, name, members)

    def class_declaration(self) -> _stmt.ClassDeclStmt:
        start = self.advance(); name = self.identifier("class 名が必要です"); self.consume(TokenType.LBRACE, "class の本体に '{' が必要です")
        members: list[_stmt.ClassMemberStmt] = []
        while not self.check(TokenType.RBRACE):
            if self.match(TokenType.STRUCT):
                token = self.previous()
                if self.match(TokenType.USE):
                    target = self.identifier("struct use の対象が必要です"); self.consume(TokenType.SEMI, "struct use の末尾に ';' が必要です")
                    members.append(_stmt.StructUseStmt(token.line, token.column, token.len, target))
                else: members.append(self.struct_declaration(token))
            elif self.match(TokenType.IMPL): members.append(self.impl_declaration(self.previous()))
            else: raise self.error_at(self.peek(), "class には struct または impl だけを書けます")
        self.advance(); return _stmt.ClassDeclStmt(start.line, start.column, start.len, name, members)

    def struct_declaration(self, start: Token) -> _stmt.StructDeclStmt:
        self.consume(TokenType.LBRACE, "struct の本体に '{' が必要です"); members: list[_stmt.VarDeclStmt] = []
        while not self.check(TokenType.RBRACE):
            if not self.check(TokenType.VAR): raise self.error_at(self.peek(), "struct には var 宣言だけを書けます")
            members.append(self.var_statement())
        self.advance(); return _stmt.StructDeclStmt(start.line, start.column, start.len, members)

    def impl_declaration(self, start: Token) -> _stmt.ClassMemberStmt:
        interface = self.identifier("impl use の対象 interface が必要です") if self.match(TokenType.USE) else None
        self.consume(TokenType.LBRACE, "impl の本体に '{' が必要です"); members: list[_stmt.FunctionDefStmt] = []
        while not self.check(TokenType.RBRACE):
            if not self.check(TokenType.DEF): raise self.error_at(self.peek(), "impl には def 宣言だけを書けます")
            members.append(self.function_definition())
        self.advance()
        return _stmt.ImplUseStmt(start.line, start.column, start.len, interface, members) if interface else _stmt.ImplStmt(start.line, start.column, start.len, members)

    # Types
    def bindings(self) -> list[_base.Binding]:
        result: list[_base.Binding] = []
        while self.match(TokenType.AT): result.append(_base.Binding(self.identifier("'@' の後に binding 名が必要です")))
        return result
    def type_node(self) -> _base.TypeNode:
        base_name = self.type_identifier("型名が必要です")
        if not self.match(TokenType.LBRACKET):
            return _base.Name(_base.TypeSyn(False, base_name, self.bindings()))
        args: list[_base.TypeSyn] = []
        while not self.check(TokenType.RBRACKET):
            is_ref = self.match(TokenType.REF); arg = self.type_identifier("コンテナ型の引数が必要です")
            args.append(_base.TypeSyn(is_ref, arg, self.bindings()))
            if not self.match(TokenType.COMMA): break
        self.consume(TokenType.RBRACKET, "コンテナ型を ']' で閉じてください")
        base = _base.Name(_base.TypeSyn(False, base_name, self.bindings()))
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
                index=self.expression(); end=self.consume(TokenType.RBRACKET,"添字を ']' で閉じてください")
                value=_expr.IndexExpr(end.line,end.column,end.len,value,index)
            elif self.match(TokenType.DOT):
                name=self.identifier("'.' の後にメンバー名が必要です"); token=self.previous()
                value=_expr.MemberExpr(token.line,token.column,token.len,value,name)
            else: return value
    def primary(self) -> _expr.Expr:
        token=self.advance()
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
            value=self.expression(); self.consume(TokenType.RPAREN,"式を ')' で閉じてください"); return value
        raise self.error_at(token, f"式として使えないトークンです: {token.value!r}")
