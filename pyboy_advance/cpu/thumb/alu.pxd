from libc.stdint cimport uint32_t

cdef void thumb_move_shifted_register(object, uint32_t) noexcept
cdef void thumb_add_subtract(object, uint32_t) noexcept
cdef void thumb_move_compare_add_subtract(object, uint32_t) noexcept
cdef void thumb_alu(object, uint32_t) noexcept
cdef void thumb_high_reg_branch_exchange(object, uint32_t) noexcept
cdef void thumb_add_offset_to_stack_pointer(object, uint32_t) noexcept
cdef void thumb_get_address(object, uint32_t) noexcept
