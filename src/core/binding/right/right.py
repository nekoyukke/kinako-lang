from dataclasses import dataclass

from enum import Enum

class AccessKind(Enum):
    NON = 0
    READ = 1
    WRITE = 2

class IdentityKind(Enum):
    SHARED = 0
    UNIQUE = 1

@dataclass
class Right():
    access: AccessKind
    identity: IdentityKind