"""Public interface for the semantic checker.

Import checker components from this package rather than its implementation
module so callers are insulated from internal module layout changes.
"""

from src.frontend.checker.checker import CheckResult, Checker, ExprResult
from src.utils.error.checker import KinakoCheckerError

# Keep the concise frontend-facing name consistent with CollectorError and
# ResolverError, while retaining the concrete exception as a public alias.
CheckerError = KinakoCheckerError

__all__ = [
    "CheckResult",
    "Checker",
    "CheckerError",
    "ExprResult",
    "KinakoCheckerError",
]
