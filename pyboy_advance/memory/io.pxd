cimport cython

from libc.stdint cimport uint8_t, uint32_t

from pyboy_advance.interrupt_controller cimport InterruptController
from pyboy_advance.keypad cimport Keypad
from pyboy_advance.memory.constants cimport IOAddress
from pyboy_advance.memory.dma cimport DMAController
from pyboy_advance.memory.memory cimport Memory
from pyboy_advance.ppu.constants cimport WindowIndex
from pyboy_advance.ppu.ppu cimport PPU
from pyboy_advance.utils cimport get_bit

cdef class IO:
    cdef Memory memory
    cdef InterruptController interrupt_controller
    cdef DMAController dma_controller
    cdef PPU ppu
    cdef Keypad keypad
    cdef uint32_t reg_soundbias

    cdef uint32_t read_32(self, uint32_t) noexcept
    cdef uint32_t read_16(self, uint32_t) noexcept
    cdef uint32_t read_8(self, uint32_t) noexcept

    cdef void write_32(self, uint32_t, uint32_t) noexcept

    @cython.locals(mask=uint32_t)
    cdef void write_16(self, uint32_t, uint32_t) noexcept

    cdef void write_8(self, uint32_t, uint32_t) noexcept
