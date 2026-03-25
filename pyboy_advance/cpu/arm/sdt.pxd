from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU
from pyboy_advance.memory.constants cimport MemoryAccess
from pyboy_advance.utils cimport get_bit, get_bits, add_32

cdef void arm_single_data_transfer(CPU, uint32_t) noexcept
