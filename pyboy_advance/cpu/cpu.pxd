from libc.stdint cimport uint32_t

ctypedef void (*InstrHandler)(object, uint32_t) noexcept

cdef struct InstrPattern:
    uint32_t mask
    uint32_t value
    InstrHandler handler
