from src.core.context.context import *
from src.core.contract.right.right import *
from src.core.contract.type.type import *
from src.core.contract.policy.policy import *
from src.core.source.source_span import *

zero = SourceSpan(0,0,0)

def inject_builtin_types(ctx:Context):
    ctx.buildin_type["int"] = ctx.intern_type(IntType(32))
    ctx.buildin_type["bool"] = ctx.intern_type(BooleanType())

def inject_builtin_rights(ctx:Context):
    ctx.right["Unique"] = RealRight(AccessKind.NONE, IdentityKind.UNIQUE)
    ctx.right["Shared"] = RealRight(AccessKind.NONE, IdentityKind.SHARED)

def inject_builtin_policies(ctx:Context):
    ctx.policy["Arc"] = Arc()
    ctx.policy["Mutex"] = Mutex()

def inject_builtins(ctx: Context) -> Context:
    inject_builtin_types(ctx)
    inject_builtin_rights(ctx)
    inject_builtin_policies(ctx)
    return ctx
