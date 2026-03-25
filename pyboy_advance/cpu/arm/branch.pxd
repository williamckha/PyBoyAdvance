from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU
from pyboy_advance.utils cimport extend_sign_24, get_bit, add_32

cdef void arm_branch(CPU, uint32_t) noexcept
cdef void arm_branch_exchange(CPU, uint32_t) noexcept
