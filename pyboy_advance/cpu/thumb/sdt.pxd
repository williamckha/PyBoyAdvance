from libc.stdint cimport uint32_t

cdef void thumb_pc_relative_load(object, uint32_t) noexcept
cdef void thumb_load_store_sign_extended(object, uint32_t) noexcept
cdef void thumb_load_store_register_offset(object, uint32_t) noexcept
cdef void thumb_load_store_immediate_offset(object, uint32_t) noexcept
cdef void thumb_load_store_halfword(object, uint32_t) noexcept
cdef void thumb_sp_relative_load_store(object, uint32_t) noexcept
