from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU

cdef void arm_multiply(CPU, uint32_t) noexcept
cdef void arm_multiply_long(CPU, uint32_t) noexcept
