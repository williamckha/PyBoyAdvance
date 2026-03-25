from libc.stdint cimport uint32_t

from pyboy_advance.cpu.cpu cimport CPU

cdef void thumb_pc_relative_load(CPU, uint32_t) noexcept
cdef void thumb_load_store_sign_extended(CPU, uint32_t) noexcept
cdef void thumb_load_store_register_offset(CPU, uint32_t) noexcept
cdef void thumb_load_store_immediate_offset(CPU, uint32_t) noexcept
cdef void thumb_load_store_halfword(CPU, uint32_t) noexcept
cdef void thumb_sp_relative_load_store(CPU, uint32_t) noexcept
