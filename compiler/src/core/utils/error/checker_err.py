from src.core.span import Span

class CheckerError(ValueError):
    def __init__(
        self,
        source: str,
        span: Span,
        message: str,
        expected: str | None = None,
        actual: str | None = None,
        context: str | None = None,
    ):
        self.source = source
        self.span = span
        self.message = message
        self.expected = expected
        self.actual = actual
        self.context = context

        details = [message]

        if expected is not None:
            details.append(f"Expected: {expected}")

        if actual is not None:
            details.append(f"Got: {actual}")

        if context is not None:
            details.append(f"Context: {context}")

        super().__init__(
            f"{' | '.join(details)} "
            f"at {span.start}:{span.end}"
        )