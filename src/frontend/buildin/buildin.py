"""Register frontend built-ins in a compilation context."""

from src.core.context.context import context
from src.core.binding.type import type
from src.core.binding.right import right
from src.core.binding.policy import policy

def add_buildins(target: context) -> None:
    """Add built-in types, rights, policies, and declarations to ``target``."""
    target.general.types["char"] = type.IntType(8, True)
    target.general.types["short"] = type.IntType(16, True)
    target.general.types["int"] = type.IntType(32, True)
    target.general.types["long"] = type.IntType(64, True)

    target.general.types["i8"] = type.IntType(8, True)
    target.general.types["i16"] = type.IntType(16, True)
    target.general.types["i32"] = type.IntType(32, True)
    target.general.types["i64"] = type.IntType(64, True)
    target.general.types["u8"] = type.IntType(8, False)
    target.general.types["u16"] = type.IntType(16, False)
    target.general.types["u32"] = type.IntType(32, False)
    target.general.types["u64"] = type.IntType(64, False)

    target.general.types["float"] = type.FloatType(32)

    target.general.types["none"] = type.NoneType()

    target.general.rights["owner"] = right.Right(right.AccessKind.WRITE, right.IdentityKind.UNIQUE)
    target.general.rights["mutable"] = right.Right(right.AccessKind.READ, right.IdentityKind.UNIQUE)
    target.general.rights["shared"] = right.Right(right.AccessKind.READ, right.IdentityKind.SHARED)
    target.general.rights["multi"] = right.Right(right.AccessKind.WRITE, right.IdentityKind.SHARED)


    target.general.default_policy = policy.NoPolicy()
    target.general.default_right = right.Right(right.AccessKind.READ, right.IdentityKind.UNIQUE)
