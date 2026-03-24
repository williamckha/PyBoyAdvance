from libc.stdint cimport uint32_t

cdef void arm_msr(object, uint32_t) noexcept
cdef void arm_mrs(object, uint32_t) noexcept
