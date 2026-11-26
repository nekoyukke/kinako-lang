class LexerError(ValueError):
    def __init__(self, source: str, position: int):
        self.source = source
        self.position = position

        char = source[position]
        super().__init__(
            f"Unexpected character {char!r} "
            f"at position {position}"
        )