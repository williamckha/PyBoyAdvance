from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU
from pyboy_advance.cpu.constants cimport Condition
from pyboy_advance.memory.constants cimport MemoryAccess
from pyboy_advance.utils cimport (
    get_bits,
    extend_sign_12,
    extend_sign_8,
    get_bit,
    add_32,
    extend_sign_23,
)

cdef void thumb_unconditional_branch(CPU, uint32_t) noexcept
cdef void thumb_conditional_branch(CPU, uint32_t) noexcept
cdef void thumb_long_branch_with_link(CPU, uint32_t) noexcept
