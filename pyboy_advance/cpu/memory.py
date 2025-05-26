from enum import Enum


class MemoryAccess(Enum):
    NON_SEQUENTIAL = 0
    SEQUENTIAL = 1


class Memory:

    def read_32(self, address: int, access_type: MemoryAccess) -> int:
        pass

    def read_16(self, address: int, access_type: MemoryAccess) -> int:
        pass
