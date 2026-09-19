import re

from src.core.token.token import Token
from src.core.token.tokentype import TokenType
from src.utils.error.code import ErrorCode
from src.utils.error.syntax import KinakoSyntaxError

class Lexer():
    def __init__(self, source:str) -> None:
        self.source = source
        self.REGEX = self.build_regex()

    def build_regex(self):
        # EOF is an explicit sentinel appended after scanning.  Including its
        # empty regular expression here lets ``finditer`` fabricate EOF tokens
        # in the middle of invalid input.
        # TokenType is deliberately ordered so keywords precede ID and each
        # multi-character operator precedes its prefix operator.
        token_types = [token_type for token_type in TokenType if token_type is not TokenType.EOF]
        patterns = [f"(?P<{token_type.name}>{token_type.value})" for token_type in token_types]

        return re.compile("|".join(patterns))

    def error_at(
        self, code: ErrorCode, token: Token, detail: str | None = None
    ) -> KinakoSyntaxError:
        message = f"[{code.code}] {code.message}"
        if detail is not None:
            message = f"{message}: {detail}"
        return KinakoSyntaxError(
            message, token.line, token.column, self.source, token.len
        )

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        offset = 0
        while offset < len(self.source):
            mo = self.REGEX.match(self.source, offset)
            if mo is None:
                line = self.source.count("\n", 0, offset) + 1
                column = offset - self.source.rfind("\n", 0, offset)
                token = Token(TokenType.EOF, self.source[offset], line, column, 1)
                raise self.error_at(
                    ErrorCode.LEX_UNEXPECTED_CHARACTER, token, self.source[offset]
                )
            kind_name = mo.lastgroup
            value = mo.group()
            start = mo.start()
            line = self.source.count("\n", 0, start) + 1
            col = start - self.source.rfind("\n", 0, start)
            if kind_name is None:
                token = Token(TokenType.EOF, value, line, col, len(value))
                raise self.error_at(ErrorCode.LEX_INVALID_TOKEN_PATTERN, token)
        
            # kind_name (Enumの名前) から直接 Enumオブジェクトを取得
            kind = TokenType[kind_name]
        
            match (kind):
                case TokenType.SKIP:
                    pass
                case TokenType.COMMENT:
                    pass
                case _:
                    # Token生成
                    tokens.append(Token(kind, value, line, col, len(value)))
            offset = mo.end()
        final_line = self.source.count("\n") + 1
        final_column = len(self.source) - self.source.rfind("\n")
        tokens.append(Token(TokenType.EOF, "", final_line, final_column, 0))
        return tokens
