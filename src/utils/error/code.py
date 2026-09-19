"""Stable error codes and their default messages."""

from enum import Enum


class ErrorCode(Enum):
    INTERNAL_UNSUPPORTED_AST = ("K0001", "unsupported AST")
    INTERNAL_INVALID_COLLECTED_SYMBOL = ("K0002", "invalid collected symbol")
    INTERNAL_INVALID_SCOPE_EXIT = ("K0003", "cannot leave the root scope")

    SYNTAX_EXPECTED_TOKEN = ("K1001", "expected token")
    SYNTAX_EXPECTED_TYPE = ("K1002", "expected type")
    SYNTAX_UNSUPPORTED_STATEMENT = ("K1003", "unsupported statement")
    SYNTAX_UNCLOSED_BLOCK = ("K1004", "unclosed block")
    SYNTAX_INVALID_RECORD_MEMBER = ("K1005", "invalid record member")
    SYNTAX_INVALID_INTERFACE_MEMBER = ("K1006", "invalid interface member")
    SYNTAX_INVALID_CLASS_MEMBER = ("K1007", "invalid class member")
    SYNTAX_INVALID_STRUCT_MEMBER = ("K1008", "invalid struct member")
    SYNTAX_INVALID_IMPL_MEMBER = ("K1009", "invalid impl member")
    SYNTAX_INVALID_EXPRESSION = ("K1010", "invalid expression")

    LEX_UNEXPECTED_CHARACTER = ("K1101", "unexpected character")
    LEX_INVALID_TOKEN_PATTERN = ("K1102", "invalid token pattern")

    COLLECT_DUPLICATE_DECLARATION = ("K2001", "duplicate declaration")
    COLLECT_DUPLICATE_TYPE = ("K2002", "duplicate type declaration")
    COLLECT_UNSUPPORTED_TYPE_CONTRACT = ("K2003", "unsupported type contract")
    COLLECT_UNKNOWN_TYPE = ("K2004", "unknown type")
    COLLECT_UNKNOWN_BINDING = ("K2005", "unknown right or policy")

    RESOLVE_UNKNOWN_NAME = ("K3001", "unknown name")
    RESOLVE_DUPLICATE_DECLARATION = ("K3002", "duplicate declaration in scope")
    RESOLVE_UNKNOWN_TYPE = ("K3003", "unknown type")
    RESOLVE_UNKNOWN_BINDING = ("K3004", "unknown right or policy")
    RESOLVE_UNKNOWN_RECORD = ("K3005", "unknown record")
    RESOLVE_UNKNOWN_INTERFACE = ("K3006", "unknown interface")
    RESOLVE_INVALID_STRUCT_SYMBOL = ("K3007", "collector symbol is not a struct")
    RESOLVE_INVALID_IMPL_SYMBOL = ("K3008", "collector symbol is not an impl")
    RESOLVE_INVALID_LEXICAL_SYMBOL = ("K3009", "symbol cannot be declared in a lexical scope")
    RESOLVE_MISSING_COLLECTED_SYMBOL = ("K3010", "collector symbol is missing")
    RESOLVE_UNSUPPORTED_TYPE_CONTRACT = ("K3011", "unsupported type contract")

    CHECK_UNSUPPORTED_AST = ("K4001", "unsupported AST")  # 未対応の AST
    CHECK_GENERIC_ARITHMETIC = ("K4002", "arithmetic operands cannot be generic")  # 算術演算にジェネリック型は使えない
    CHECK_UNKNOWN_SYMBOL = ("K4003", "unknown symbol")  # 不明なシンボル
    CHECK_MISSING_BINDING = ("K4004", "missing binding")  # Binding が存在しない
    CHECK_INVALID_ASSIGNMENT_TARGET = ("K4005", "invalid assignment target")  # 代入先として不正
    CHECK_ASSIGNMENT_TYPE_MISMATCH = ("K4006", "assignment type mismatch")  # 代入時の型不一致
    CHECK_ASSIGN_TO_IMMUTABLE = ("K4007", "cannot assign to immutable value")  # 不変値への代入
    CHECK_BINARY_OPERAND_TYPE_MISMATCH = ("K4008", "binary operand type mismatch")  # 二項演算の型不一致
    CHECK_ARITHMETIC_OPERAND_NOT_NUMERIC = ("K4009", "arithmetic operand is not numeric")  # 算術演算の対象が数値ではない
    CHECK_LOGIC_OPERAND_NOT_BOOLEAN = ("K4010", "logical operand is not boolean")  # 論理演算の対象が真偽値ではない
    CHECK_COMPARISON_OPERAND_TYPE_MISMATCH = ("K4011", "comparison operand type mismatch")  # 比較演算の型不一致
    CHECK_IDENTITY_OPERAND_TYPE_MISMATCH = ("K4012", "identity operand type mismatch")  # 同一性比較の型不一致
    CHECK_INDEX_TARGET_NOT_INDEXABLE = ("K4013", "index target is not indexable")  # 添字アクセスできない値
    CHECK_INDEX_NOT_INTEGER = ("K4014", "index is not an integer")  # 添字が整数ではない
    CHECK_UNKNOWN_MEMBER = ("K4015", "unknown member")  # 不明なメンバー
    CHECK_CONDITION_NOT_BOOLEAN = ("K4016", "condition is not boolean")  # 条件式が真偽値ではない
    CHECK_RETURN_OUTSIDE_FUNCTION = ("K4017", "return outside function")  # 関数外の return
    CHECK_RETURN_TYPE_MISMATCH = ("K4018", "return type mismatch")  # 戻り値の型不一致
    CHECK_MISSING_RETURN = ("K4019", "missing return")  # 必要な return がない
    CHECK_FUNCTION_ARGUMENT_COUNT_MISMATCH = ("K4020", "function argument count mismatch")  # 引数の個数不一致
    CHECK_FUNCTION_ARGUMENT_TYPE_MISMATCH = ("K4021", "function argument type mismatch")  # 引数の型不一致
    CHECK_UNKNOWN_INTERFACE_REQUEST = ("K4022", "unknown interface request")  # 不明な interface 要求
    CHECK_IMPL_MISSING_DEFINITION = ("K4023", "implementation is missing a definition")  # impl に必要な定義がない
    CHECK_IMPL_UNEXPECTED_DEFINITION = ("K4024", "implementation has an unexpected definition")  # impl に不要な定義がある
    CHECK_IMPL_PARAMETER_COUNT_MISMATCH = ("K4025", "implementation parameter count mismatch")  # impl 引数の個数不一致
    CHECK_IMPL_PARAMETER_TYPE_MISMATCH = ("K4026", "implementation parameter type mismatch")  # impl 引数の型不一致
    CHECK_IMPL_RETURN_TYPE_MISMATCH = ("K4027", "implementation return type mismatch")  # impl 戻り値の型不一致
    CHECK_CONTAINER_ELEMENT_TYPE_MISMATCH = ("K4028", "container element type mismatch")  # コンテナ要素の型不一致
    CHECK_INVALID_MOVE = ("K4029", "invalid move")  # 不正な move
    CHECK_INVALID_REFERENCE = ("K4030", "invalid reference")  # 不正な ref
    CHECK_USE_AFTER_MOVE = ("K4031", "use after move")  # move 後の利用
    CHECK_RIGHT_VIOLATION = ("K4032", "right violation")  # Right 違反
    CHECK_POLICY_VIOLATION = ("K4033", "policy violation")  # Policy 違反

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
