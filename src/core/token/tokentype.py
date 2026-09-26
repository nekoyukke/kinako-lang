from enum import Enum

class TokenType(Enum):
    # 演算子
    COMMENT = r'//[^\n]*'
    
    DOT = r'\.'
    ARROW = r'->'

    EQ = r'=='
    NE = r'!='
    LE = r'<='
    GE = r'>='
    PLUS_ASSIGN = r'\+='
    
    PLUS = r'\+'
    MINUS = r'-'
    MULT = r'\*'
    DIV = r'/'
    MOD = r'%'
    LOGIC_OR = r'\|\|'
    LOGIC_AND = r'&&'
    AT = r'@'

    ASSIGN = r'='
    # リテラル
    NONE = r'none\b'
    NULL = r'null\b'
    
    UNION = r'\|'

    # 構文
    IF = r'if\b'
    ELSE = r'else\b'
    ELIF = r'elif\b'
    FOR = r'for\b'
    WHILE = r'while\b'
    FN = r'fn\b'
    RETURN = r'return\b'
    IN = r'in\b'
    LET = r'let\b'
    CLASS = r'class\b'
    MOVE = r'move\b'
    REF = r'ref\b'
    AS = r'as\b'
    UNSAFE = r'unsafe\b'
    ASM = r'__asm__\b'

    RECORD = r'record\b'
    IMPL = r'impl\b'
    STRUCT = r'struct\b'
    VAR = r'var\b'
    INTERFACE = r'interface\b'
    RQ = r'rq\b'
    DEF = r'def\b'

    USE = r'use\b'

    # キーワード
    LABRACKET = r'<'
    RABRACKET = r'>'
    LPAREN = r'\('
    RPAREN = r'\)'
    LBRACE = r'\{'
    RBRACE = r'\}'
    LBRACKET = r'\['
    RBRACKET = r'\]'
    SEMI = r';'
    COMMA = r','
    COLON = r':'

    # 可変
    DECIMAL = r'\d+\.\d+'
    STRING = r'"(\\.|[^"\\])*"'
    NUMBER  = r'\d+'
    SKIP = r'\s+'
    ID = r'[a-zA-Z_][a-zA-Z0-9_]*'


    # 特殊
    EOF = ""
