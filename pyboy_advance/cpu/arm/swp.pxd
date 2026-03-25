from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU

cdef void arm_single_data_swap(CPU, uint32_t) noexcept
