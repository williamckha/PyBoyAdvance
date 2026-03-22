import cython

from libc.stdint cimport uint8_t, uint32_t, uint64_t

cdef inline bint get_bit(uint32_t, int) noexcept

cdef inline uint32_t get_bits(uint32_t, int, int) noexcept

cdef inline uint32_t set_bit(uint32_t, int, bint) noexcept

cdef inline bint sign_32(uint32_t) noexcept

cdef inline bint sign_24(uint32_t) noexcept

cdef inline bint sign_23(uint32_t) noexcept

cdef inline bint sign_16(uint32_t) noexcept

cdef inline bint sign_12(uint32_t) noexcept

cdef inline bint sign_9(uint32_t) noexcept

cdef inline bint sign_8(uint32_t) noexcept

@cython.locals(extension=uint64_t)
cdef inline uint64_t extend_sign_32(uint32_t) noexcept

@cython.locals(extension=uint32_t)
cdef inline uint32_t extend_sign_24(uint32_t) noexcept

@cython.locals(extension=uint32_t)
cdef inline uint32_t extend_sign_23(uint32_t) noexcept

@cython.locals(extension=uint32_t)
cdef inline uint32_t extend_sign_16(uint32_t) noexcept

@cython.locals(extension=uint32_t)
cdef inline uint32_t extend_sign_12(uint32_t) noexcept

@cython.locals(extension=uint32_t)
cdef inline uint32_t extend_sign_9(uint32_t) noexcept

@cython.locals(extension=uint32_t)
cdef inline uint32_t extend_sign_8(uint32_t) noexcept

@cython.locals(mask=uint32_t)
cdef inline uint32_t add_32(uint32_t, uint32_t) noexcept

@cython.locals(mask=uint32_t)
cdef inline uint32_t ror_32(uint32_t, int) noexcept

cdef inline uint32_t array_read_32(uint8_t[:], int) noexcept

cdef inline uint32_t array_read_16(uint8_t[:], int) noexcept

cdef inline void array_write_32(uint8_t[:], int, uint32_t) noexcept

cdef inline void array_write_16(uint8_t[:], int, uint32_t) noexcept
