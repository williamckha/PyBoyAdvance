from libc.stdint cimport uint8_t, uint16_t, uint32_t
from cpython.array cimport array

from pyboy_advance.constants cimport Interrupt
from pyboy_advance.interrupt_controller cimport InterruptController
from pyboy_advance.ppu.constants cimport *
from pyboy_advance.ppu.memory cimport VideoMemory
from pyboy_advance.ppu.registers cimport (
    DisplayControlRegister,
    DisplayStatusRegister,
    BackgroundControlRegister,
    WindowControlRegister,
)
from pyboy_advance.utils cimport (
    get_bit,
    get_bits,
    sign_32,
    add_32,
    extend_sign_9,
)

cdef class Object:
    cdef (uint32_t, uint32_t)[3][4] SIZES

    cdef uint32_t attr_0
    cdef uint32_t attr_1
    cdef uint32_t attr_2

    cdef uint32_t get_x(self)
    cdef uint32_t get_y(self)
    cdef bint get_affine(self)
    cdef bint get_double_size(self)
    cdef bint get_disabled(self)
    cdef int get_mode(self)
    cdef bint get_mosaic(self)
    cdef bint get_colour_256(self)
    cdef int get_shape(self)
    cdef bint get_flip_horizontal(self)
    cdef bint get_flip_vertical(self)
    cdef (uint32_t, uint32_t) get_size(self)
    cdef uint32_t get_tile_index(self)
    cdef uint32_t get_priority(self)
    cdef uint32_t get_palette_num(self)

cdef class PPU:
    cdef uint16_t[:] scanline

    cdef void hblank_start(self)
    cdef void hblank_end(self)
    cdef void _init_layers(self)
    cdef void _render_backgrounds(self)
    cdef void _render_background_text(self, int)
    cdef void _render_background_affine(self, int)
    cdef void _render_background_bitmap(self, bint, bint)
    cdef void _render_objects(self)
    cdef void _render_object(self, Object)
    cdef void _merge_layers(self)
    cdef void _merge_layer(self, uint16_t[:], int)
    cdef void _calc_window_masks(self)
    cdef WindowControlRegister _get_window_for_pixel(self, uint32_t)
    cdef uint32_t _get_palette_index(self, uint32_t, uint32_t, uint32_t, uint32_t, bint, uint32_t)
