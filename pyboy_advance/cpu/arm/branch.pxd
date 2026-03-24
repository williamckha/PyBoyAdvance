from libc.stdint cimport uint32_t

cdef void arm_branch(object, uint32_t) noexcept
cdef void arm_branch_exchange(object, uint32_t) noexcept
