from libc.stdint cimport uint32_t

cdef void thumb_unconditional_branch(object, uint32_t) noexcept
cdef void thumb_conditional_branch(object, uint32_t) noexcept
cdef void thumb_long_branch_with_link(object, uint32_t) noexcept
