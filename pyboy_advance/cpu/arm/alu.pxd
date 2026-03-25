from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU

cdef void arm_alu(CPU, uint32_t) noexcept
