from libc.stdint cimport uint32_t

cdef void thumb_software_interrupt(object, uint32_t) noexcept
