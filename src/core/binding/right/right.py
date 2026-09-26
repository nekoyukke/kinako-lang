from dataclasses import dataclass

from enum import Enum

class AccessKind(Enum):
    NON = 0
    READ = 1
    WRITE = 2
    @classmethod
    def min(cls):
        return AccessKind.NON

class IdentityKind(Enum):
    SHARED = 0
    UNIQUE = 1
    @classmethod
    def min(cls):
        return IdentityKind.SHARED

@dataclass
class Right():
    access: AccessKind
    identity: IdentityKind
