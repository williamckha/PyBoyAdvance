from pyboy_advance.ppu.constants cimport DISPLAY_WIDTH, DISPLAY_HEIGHT
from pyboy_advance.ppu.ppu cimport PPU

cdef class Screen:
    cdef PPU ppu
