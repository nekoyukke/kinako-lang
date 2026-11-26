
from __future__ import annotations

import re
from src.core.span import Span
from src.core.tokens import Tokenkind, Token
from src.core.utils.error import LexerError

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position = 0

        # Enum の定義順をそのまま優先順位として使用する。
        self._rules: list[tuple[Tokenkind, re.Pattern[str]]] = []

        for kind in Tokenkind:
            pattern = re.compile(kind.pattern)

            # 空文字列にマッチするルールは拒否する。
            # 走査が進まなくなる事故を防止する。
            if pattern.match(""):
                raise ValueError(
                    f"{kind.name} matches an empty string: "
                    f"{kind.pattern!r}"
                )

            self._rules.append((kind, pattern))

    def __iter__(self) -> Lexer:
        return self

    def __next__(self) -> Token:
        source = self.source
        size = len(source)

        while self.position < size:
            start = self.position

            for kind, pattern in self._rules:
                # 必ず現在位置からマッチさせる。
                match = pattern.match(source, start)

                if match is None:
                    continue

                end = match.end()

                # 文脈によってゼロ長マッチになるケースも拒否。
                if end == start:
                    raise ValueError(
                        f"{kind.name} matched an empty string "
                        f"at position {start}"
                    )

                self.position = end

                if kind.skip:
                    break

                span = Span(
                    len=end - start,
                    start=start,
                    end=end,
                )

                return Token(kind=kind, span=span)

            else:
                # どのルールにもマッチしない。
                raise LexerError(source, start)

        raise StopIteration

    def tokenize(self) -> list[Token]:
        return list(self)

    def reset(self) -> None:
        self.position = 0


def lex(source: str) -> list[Token]:
    return Lexer(source).tokenize()


if __name__ == "__main__":
    source = """
fn main() {
    let x:int = 2;
    x = 1;
}
"""
    tokens = lex(source)

    for token in tokens:
        text = source[token.span.start:token.span.end]
        print(
            f"{token.kind.name:12} "
            f"{token.span!r:20} "
            f"{text!r}"
        )
