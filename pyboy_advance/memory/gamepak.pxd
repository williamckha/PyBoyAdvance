from libc.stdint cimport uint8_t, uint32_t
from cpython.array cimport array

from pyboy_advance.memory.constants cimport MemoryRegion
from pyboy_advance.utils cimport array_read_32, array_read_16

cdef class GamePak:
    cdef uint8_t[:] rom

    cdef uint32_t read_32(self, uint32_t)
    cdef uint32_t read_16(self, uint32_t)
    cdef uint32_t read_8(self, uint32_t)
