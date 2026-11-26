from enum import Enum



class Tokenkind(Enum):
    # (正規表現, skip)
    #
    # 定義順が優先順位。
    # skip=True のトークンは出力しないが、走査は行う

    WHITESPACE = (r"[ \t\r\n]+", True)

    # コメント
    LINE_COMMENT = (r"//[^\r\n]*", True)

    # キーワードは識別子より先に定義する。
    # 部分一致を防ぐため、識別子の継続文字を否定する。
    IF = (r"if(?![a-zA-Z0-9_])", False)
    ELSE = (r"else(?![a-zA-Z0-9_])", False)
    WHILE = (r"while(?![a-zA-Z0-9_])", False)
    
    LET = (r"let(?![a-zA-Z0-9_])", False)
    
    PTR = (r"let(?![a-zA-Z0-9_])", False)
    REF = (r"ref(?![a-zA-Z0-9_])", False)
    MOV = (r"mov(?![a-zA-Z0-9_])", False)
    
    FN = (r"fn(?![a-zA-Z0-9_])", False)
    S_SCRIPT = (r"subscript(?![a-zA-Z0-9_])", False)
    
    RECORD = (r"record(?![a-zA-Z0-9_])", False)
    REUCT = (r"struct(?![a-zA-Z0-9_])", False)

    INTERFACE = (r"record(?![a-zA-Z0-9_])", False)
    IMPL = (r"struct(?![a-zA-Z0-9_])", False)

    CLASS = (r"record(?![a-zA-Z0-9_])", False)

    # 識別子・数値
    IDENTIFIER = (r"[a-zA-Z_][a-zA-Z0-9_]*", False)
    NUMBER = (r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", False)

    # 文字列。エスケープされた文字と通常文字を区別する。
    STRING = (
        r'"(?:[^"\\\r\n]|\\[^\r\n])*"',
        False,
    )

    # 複数文字の演算子を単一文字より先に定義する。
    EQ = (r"==", False)
    NE = (r"!=", False)
    LE = (r"<=", False)
    GE = (r">=", False)
    AND = (r"&&", False)
    OR = (r"\|\|", False)

    ASSIGN = (r"=", False)
    LT = (r"<", False)
    GT = (r">", False)
    NOT = (r"!", False)
    AT = (r"@", False)

    PLUS = (r"\+", False)
    MINUS = (r"-", False)
    STAR = (r"\*", False)
    SLASH = (r"/", False)
    PERCENT = (r"%", False)

    LPAREN = (r"\(", False)
    RPAREN = (r"\)", False)
    LBRACE = (r"\{", False)
    RBRACE = (r"\}", False)
    LBRACKET = (r"\[", False)
    RBRACKET = (r"\]", False)

    COMMA = (r",", False)
    DOT = (r"\.", False)
    SEMICOLON = (r";", False)
    COLON = (r":", False)

    @property
    def pattern(self) -> str:
        return self.value[0]

    @property
    def skip(self) -> bool:
        return self.value[1]