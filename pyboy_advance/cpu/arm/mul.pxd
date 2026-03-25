cimport cython

from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU
from pyboy_advance.cpu.arm.constants cimport MultiplyLongOpcode
from pyboy_advance.memory.constants cimport MemoryAccess
from pyboy_advance.utils cimport get_bit, get_bits, sign_32, extend_sign_32

@cython.locals(mask=uint32_t)
cdef void arm_multiply(CPU, uint32_t) noexcept

@cython.locals(mask=uint32_t)
cdef void arm_multiply_long(CPU, uint32_t) noexcept

@cython.locals(mask=uint32_t)
cdef void arm_multiply_idle(CPU, uint32_t, bint) noexcept
