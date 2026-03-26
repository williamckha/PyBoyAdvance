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
    cdef object scheduler
    cdef InterruptController interrupt_controller
    cdef DisplayControlRegister display_control
    cdef DisplayStatusRegister display_status
    cdef uint32_t vcount
    cdef BackgroundControlRegister bg_control_0
    cdef BackgroundControlRegister bg_control_1
    cdef BackgroundControlRegister bg_control_2
    cdef BackgroundControlRegister bg_control_3
    cdef uint32_t[:] bg_offset_h
    cdef uint32_t[:] bg_offset_v
    cdef uint32_t[:] window_v_min
    cdef uint32_t[:] window_v_max
    cdef uint32_t[:] window_h_min
    cdef uint32_t[:] window_h_max
    cdef WindowControlRegister window_control_0
    cdef WindowControlRegister window_control_1
    cdef WindowControlRegister window_control_obj
    cdef WindowControlRegister window_control_out
    cdef uint16_t[:] window_mask_0
    cdef uint16_t[:] window_mask_1
    cdef uint16_t[:] window_mask_obj
    cdef VideoMemory memory
    cdef uint16_t[4][240] bg_scanline
    cdef uint16_t[4][240] obj_scanline
    cdef uint16_t[240] scanline
    cdef object front_buffer
    cdef object back_buffer
    cdef object front_buffer_ptr
    cdef object back_buffer_ptr

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
    cdef BackgroundControlRegister _get_bg_control(self, int)
