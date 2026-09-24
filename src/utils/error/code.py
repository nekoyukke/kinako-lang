"""Stable error codes and their default messages."""

from enum import Enum


class ErrorCode(Enum):
    INTERNAL_UNSUPPORTED_AST = ("K0001", "unsupported AST")  # 未対応の AST
    INTERNAL_INVALID_COLLECTED_SYMBOL = ("K0002", "invalid collected symbol")  # collector の不正なシンボル
    INTERNAL_INVALID_SCOPE_EXIT = ("K0003", "cannot leave the root scope")  # ルートスコープからは抜けられない

    SYNTAX_EXPECTED_TOKEN = ("K1001", "expected token")  # 必要なトークンがない
    SYNTAX_EXPECTED_TYPE = ("K1002", "expected type")  # 型名が必要
    SYNTAX_UNSUPPORTED_STATEMENT = ("K1003", "unsupported statement")  # 未対応の文
    SYNTAX_UNCLOSED_BLOCK = ("K1004", "unclosed block")  # ブロックが閉じられていない
    SYNTAX_INVALID_RECORD_MEMBER = ("K1005", "invalid record member")  # record のメンバーが不正
    SYNTAX_INVALID_INTERFACE_MEMBER = ("K1006", "invalid interface member")  # interface のメンバーが不正
    SYNTAX_INVALID_CLASS_MEMBER = ("K1007", "invalid class member")  # class のメンバーが不正
    SYNTAX_INVALID_STRUCT_MEMBER = ("K1008", "invalid struct member")  # struct のメンバーが不正
    SYNTAX_INVALID_IMPL_MEMBER = ("K1009", "invalid impl member")  # impl のメンバーが不正
    SYNTAX_INVALID_EXPRESSION = ("K1010", "invalid expression")  # 式として不正
    SYNTAX_EXPECTED_IDENTIFIER = ("K1011", "expected identifier")  # 識別子が必要
    SYNTAX_EXPECTED_SEMICOLON = ("K1012", "expected semicolon")  # セミコロンが必要
    SYNTAX_EXPECTED_OPEN_PAREN = ("K1013", "expected opening parenthesis")  # 開き丸括弧が必要
    SYNTAX_EXPECTED_CLOSE_PAREN = ("K1014", "expected closing parenthesis")  # 閉じ丸括弧が必要
    SYNTAX_EXPECTED_OPEN_BRACE = ("K1015", "expected opening brace")  # 開き波括弧が必要
    SYNTAX_EXPECTED_CLOSE_BRACE = ("K1016", "expected closing brace")  # 閉じ波括弧が必要
    SYNTAX_EXPECTED_CLOSE_BRACKET = ("K1017", "expected closing bracket")  # 閉じ角括弧が必要
    SYNTAX_EXPECTED_COLON = ("K1018", "expected colon")  # コロンが必要
    SYNTAX_EXPECTED_ARROW = ("K1019", "expected return type arrow")  # 戻り値矢印が必要
    SYNTAX_EXPECTED_INTERFACE_REQUEST = ("K1020", "expected interface request")  # interface 要求が必要
    SYNTAX_EXPECTED_FUNCTION = ("K1021", "expected function declaration")  # 関数宣言が必要
    SYNTAX_EXPECTED_DEFINITION = ("K1022", "expected implementation definition")  # impl 定義が必要

    LEX_UNEXPECTED_CHARACTER = ("K1101", "unexpected character")  # 解釈できない文字
    LEX_INVALID_TOKEN_PATTERN = ("K1102", "invalid token pattern")  # 不正なトークン規則

    COLLECT_DUPLICATE_DECLARATION = ("K2001", "duplicate declaration")  # 宣言の重複
    COLLECT_DUPLICATE_TYPE = ("K2002", "duplicate type declaration")  # 型宣言の重複
    COLLECT_UNSUPPORTED_TYPE_CONTRACT = ("K2003", "unsupported type contract")  # 未対応の型契約
    COLLECT_UNKNOWN_TYPE = ("K2004", "unknown type")  # 不明な型
    COLLECT_UNKNOWN_BINDING = ("K2005", "unknown right or policy")  # 不明な Right または Policy

    RESOLVE_UNKNOWN_NAME = ("K3001", "unknown name")  # 不明な名前
    RESOLVE_DUPLICATE_DECLARATION = ("K3002", "duplicate declaration in scope")  # スコープ内で宣言が重複
    RESOLVE_UNKNOWN_TYPE = ("K3003", "unknown type")  # 不明な型
    RESOLVE_UNKNOWN_BINDING = ("K3004", "unknown right or policy")  # 不明な Right または Policy
    RESOLVE_UNKNOWN_RECORD = ("K3005", "unknown record")  # 不明な record
    RESOLVE_UNKNOWN_INTERFACE = ("K3006", "unknown interface")  # 不明な interface
    RESOLVE_INVALID_STRUCT_SYMBOL = ("K3007", "collector symbol is not a struct")  # struct でない collector シンボル
    RESOLVE_INVALID_IMPL_SYMBOL = ("K3008", "collector symbol is not an impl")  # impl でない collector シンボル
    RESOLVE_INVALID_LEXICAL_SYMBOL = ("K3009", "symbol cannot be declared in a lexical scope")  # 字句スコープへ置けないシンボル
    RESOLVE_MISSING_COLLECTED_SYMBOL = ("K3010", "collector symbol is missing")  # collector シンボルがない
    RESOLVE_UNSUPPORTED_TYPE_CONTRACT = ("K3011", "unsupported type contract")  # 未対応の型契約

    CHECK_UNSUPPORTED_AST = ("K4001", "unsupported AST")  # 未対応の AST
    CHECK_GENERIC_ARITHMETIC = ("K4002", "operands cannot be generic")  # 算術演算にジェネリック型は使えない
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
    CHECK_GENERIC_COMP = ("K4034", "comparison operands cannot be generic")  # 比較演算にジェネリック型は使えない
    CHECK_GENERIC_IDEN = ("K4035", "identity operands cannot be generic")  # 同値演算にジェネリック型は使えない
    CHECK_CANT_READ = ("K4036", "can not read right")  # Right 読めない
    CHECK_IDENTITY_OPERAND_GENERIC = ("K4037", "identity operands cannot be generic")  # 同一性比較の型不一致
    CHECK_COMPARISON_OPERAND_GENERIC = ("K4038", "comparison operands cannot be generic")  # 比較演算にジェネリック型は使えない
    CHECK_PARTIAL_MOVE_FORBIDDEN = ("K4039", "cannot move a field or indexed element")  # field/index の move は禁止
    CHECK_PARTIAL_REFERENCE_FORBIDDEN = ("K4040", "cannot reference a field or indexed element")  # field/index の ref は禁止
    CHECK_IMPL_RECEIVER_MISSING = ("K4041", "implementation definition requires an explicit receiver")  # impl def の receiver がない
    CHECK_IMPL_RECEIVER_TYPE_MISMATCH = ("K4042", "implementation receiver must have the enclosing class type")  # impl def の receiver 型が Class と違う
    CHECK_MISSING_INITIALIZER = ("K4043", "declaration requires an initializer")  # 初期値が必要
    CHECK_REFERENCE_INITIALIZER_REQUIRED = ("K4044", "let reference binding requires a ref initializer")  # let の ref 型には ref 初期化が必要
    CHECK_REFERENCE_MOVE_FORBIDDEN = ("K4045", "cannot initialize a reference binding with move")  # ref 型を move で初期化できない
    CHECK_REFERENCE_TARGET_NOT_REFERENCE = ("K4046", "reference target must have a ref binding")  # ref の借用先は ref 型でなければならない
    CHECK_REFERENCE_TARGET_OUTLIVES_SOURCE = ("K4047", "reference target must not outlive its source")  # ref の借用先が貸与元より長命
    CHECK_REFERENCE_TARGET_ALREADY_ACTIVE = ("K4048", "reference target already has an active reference")  # ref の借用先は二重にできない
    CHECK_CONDITIONAL_MOVE_MISMATCH = ("K4049", "move differs between control-flow paths")  # 分岐経路ごとに move 元／先が異なる

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
