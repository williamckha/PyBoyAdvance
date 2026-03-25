from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU

cdef void thumb_move_shifted_register(CPU, uint32_t) noexcept
cdef void thumb_add_subtract(CPU, uint32_t) noexcept
cdef void thumb_move_compare_add_subtract(CPU, uint32_t) noexcept
cdef void thumb_alu(CPU, uint32_t) noexcept
cdef void thumb_high_reg_branch_exchange(CPU, uint32_t) noexcept
cdef void thumb_add_offset_to_stack_pointer(CPU, uint32_t) noexcept
cdef void thumb_get_address(CPU, uint32_t) noexcept
