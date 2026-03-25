cimport cython

from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU
from pyboy_advance.cpu.constants cimport CPUMode
from pyboy_advance.memory.constants cimport MemoryAccess
from pyboy_advance.utils cimport get_bits, get_bit, ror_32

cdef void arm_mrs(CPU, uint32_t) noexcept

@cython.locals(mask=uint32_t, flags_mask=uint32_t, status_mask=uint32_t, extension_mask=uint32_t, control_mask=uint32_t)
cdef void arm_msr(CPU, uint32_t) noexcept
