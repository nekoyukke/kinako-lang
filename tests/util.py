from src.frontend.lexer.lexer import *
from src.frontend.parser.parser import *
from src.core.ast.stmt import *
from src.core.context.context import *
from src.utils.error.error_lists import *
from src.frontend.builtin.builtin import *
from src.frontend.resolver.resolver import *


def lexer(source:str):
    return Lexer(source).tokenize()

def parser(source:str, tb:bool=False):
    toks = lexer(source)
    pas = Parser(toks, source)
    stmt = pas.parse()
    print(ErrorLists(pas.error).__str__(tb))
    return stmt

def builtin(context:Context | None = None):
    ctx = Context() if context is None else context
    inject_builtins(ctx)
    return ctx

def collector(source:str, program:ProgramStmt, tb:bool=False, context:Context | None = None):
    # Top-level collection is now Resolver's first pass.
    return builtin(context)

def resolver(source:str, program:ProgramStmt, ctx:Context, tb:bool=False):
    rso = Resolver(program, source, ctx)
    rso.resolve()
    print(ErrorLists(rso.error).__str__(tb))
    return ctx
