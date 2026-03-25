from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU

cdef void arm_branch(CPU, uint32_t) noexcept
cdef void arm_branch_exchange(CPU, uint32_t) noexcept
