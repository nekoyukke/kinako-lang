from dataclasses import dataclass
from enum import Enum

class AccessKind(Enum):
    NONE = 0
    READ = 1
    WRITE = 2

class IdentityKind(Enum):
    SHARED = 0
    UNIQUE = 1

@dataclass
class Right():
    access: AccessKind
    identity: IdentityKind
    generic: Right | None = None

    @classmethod
    def default(cls):
        return Right(AccessKind.READ, IdentityKind.UNIQUE)