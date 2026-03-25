from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU

cdef void thumb_unconditional_branch(CPU, uint32_t) noexcept
cdef void thumb_conditional_branch(CPU, uint32_t) noexcept
cdef void thumb_long_branch_with_link(CPU, uint32_t) noexcept
