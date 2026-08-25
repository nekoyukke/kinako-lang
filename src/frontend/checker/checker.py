
import src.core.ast.base as _base
import src.core.ast.stmt as _stmt
import src.core.ast.expr as _expr
from src.core.context.context import Context, ExprInfo
from src.utils.error.base import KinakoBaseError, KinakoHelp, KinakoRelatedInfo
from src.utils.error.type import KinakoTypeError

class Checker:
    """Single-pass semantic-checker skeleton.

    Every expression is visited once and returns ExprInfo. Type, Right, and
    Policy rules will be added to these branches without introducing separate
    AST passes.
    """

    def __init__(self, source: str, program: _stmt.ProgramStmt, ctx: Context) -> None:
        self.source = source
        self.program = program
        self.ctx = ctx
        self.error: list[KinakoBaseError] = []
        self.current_function: _stmt.FunctionDeclStmt | None = None

    def call_error(
        self,
        message: str,
        node: _base.ASTNode,
        related: list[KinakoRelatedInfo] | None = None,
        help: list[KinakoHelp] | None = None,
    ) -> KinakoTypeError:
        err = KinakoTypeError(message, node.line, node.col, self.source, node.len, related, help)
        self.error.append(err)
        return err

    def check(self) -> None:
        for statement in self.program.instr:
            self.check_stmt(statement)

    # Compatibility with the previous unfinished API.
    def visit(self) -> None:
        self.check()

    def check_stmt(self, node: _stmt.Stmt) -> None:
        match node:
            case _stmt.VariableDeclStmt():
                if node.left:self.check_expr(node.left)
                return

            case _stmt.FunctionDeclStmt():
                previous = self.current_function
                self.current_function = node
                self.check_stmt(node.body)
                self.current_function = previous
                return

            case _stmt.BlockStmt():
                for statement in node.instr:
                    self.check_stmt(statement)
                return

            case _stmt.ExprStmt():
                self.check_expr(node.expr)
                return
            
            case _stmt.ReturnStmt():
                self.check_expr(node.expr)
                return

            case _stmt.Ifstmt(cond=cond, then_stmt=then_stmt, else_stmt=else_stmt):
                self.check_expr(cond)
                self.check_stmt(then_stmt)
                if else_stmt is not None:
                    self.check_stmt(else_stmt)
                return

            case _stmt.WhileStmt(cond=cond, loop=loop):
                self.check_expr(cond)
                self.check_stmt(loop)
                return

            case _stmt.ForEachStmt(iterator=iterator, loop=loop):
                self.check_expr(iterator)
                self.check_stmt(loop)
                return

            case _:
                raise

    # Compatibility with the previous unfinished API.
    def visit_stmt(self, node: _stmt.Stmt) -> None:
        self.check_stmt(node)

    def check_expr(self, node: _expr.Expr) -> ExprInfo:
        """Visit one expression once and return its future semantic result."""
        match node:
            case _expr.Variable() | _expr.Literal():
                return ExprInfo()

            case _expr.UnaryExpr():
                self.check_expr(node.expr)
                return ExprInfo()

            case (
                _expr.BinaryExpr()
                | _expr.LogicExpr()
                | _expr.AssignExpr()
            ):
                self.check_expr(node.left)
                self.check_expr(node.right)
                return ExprInfo()

            case _expr.CallExpr():
                self.check_expr(node.call)
                for argument in node.args:
                    self.check_expr(argument)
                return ExprInfo()

            case _expr.IndexExpr():
                self.check_expr(node.expr)
                self.check_expr(node.index)
                return ExprInfo()

            case _expr.MemberExpr():
                self.check_expr(node.expr)
                return ExprInfo()

            case _:
                return ExprInfo()


# Keep current imports working while callers migrate to Checker.
TypeChecker = Checker
