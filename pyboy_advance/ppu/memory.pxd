from libc.stdint cimport uint8_t, uint32_t
from cpython.array cimport array

from pyboy_advance.memory.constants cimport MemoryRegion
from pyboy_advance.ppu.constants cimport VideoMode
from pyboy_advance.ppu.registers cimport DisplayControlRegister
from pyboy_advance.utils cimport (
    get_bit,
    array_read_32,
    array_read_16,
    array_write_32,
    array_write_16,
)

cdef class VideoMemory:
    cdef DisplayControlRegister display_control
    cdef uint8_t[:] palram
    cdef uint8_t[:] vram
    cdef uint8_t[:] oam

    cdef uint32_t read_32_palram(self, uint32_t)
    cdef uint32_t read_32_vram(self, uint32_t)
    cdef uint32_t read_32_oam(self, uint32_t)
    cdef uint32_t read_16_palram(self, uint32_t)
    cdef uint32_t read_16_vram(self, uint32_t)
    cdef uint32_t read_16_oam(self, uint32_t)
    cdef uint32_t read_8_palram(self, uint32_t)
    cdef uint32_t read_8_vram(self, uint32_t)
    cdef uint32_t read_8_oam(self, uint32_t)
    cdef void write_32_palram(self, uint32_t, uint32_t)
    cdef void write_32_vram(self, uint32_t, uint32_t)
    cdef void write_32_oam(self, uint32_t, uint32_t)
    cdef void write_16_palram(self, uint32_t, uint32_t)
    cdef void write_16_vram(self, uint32_t, uint32_t)
    cdef void write_16_oam(self, uint32_t, uint32_t)
    cdef void write_8_palram(self, uint32_t, uint32_t)
    cdef void write_8_vram(self, uint32_t, uint32_t)
    cdef uint32_t _get_vram_address_mask(self, uint32_t)
