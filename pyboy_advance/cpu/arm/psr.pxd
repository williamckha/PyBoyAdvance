from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU

cdef void arm_msr(CPU, uint32_t) noexcept
cdef void arm_mrs(CPU, uint32_t) noexcept
