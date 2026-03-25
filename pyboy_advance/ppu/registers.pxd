from libc.stdint cimport uint32_t

from pyboy_advance.utils cimport get_bits, get_bit, set_bit

cdef class DisplayControlRegister:
    cdef uint32_t reg

    cdef int get_video_mode(self)
    cdef bint get_page_select(self)
    cdef bint get_hblank_interval_free(self)
    cdef bint get_obj_vram_dimension(self)
    cdef bint get_force_blank(self)
    cdef bint display_bg(self, int)
    cdef bint get_display_obj(self)
    cdef bint display_window(self, int)

cdef class DisplayStatusRegister:
    cdef uint32_t reg

    cdef bint get_vblank_status(self)
    cdef void set_vblank_status(self, bint)
    cdef bint get_hblank_status(self)
    cdef void set_hblank_status(self, bint)
    cdef bint get_vcount_trigger_status(self)
    cdef void set_vcount_trigger_status(self, bint)
    cdef bint get_vblank_irq(self)
    cdef void set_vblank_irq(self, bint)
    cdef bint get_hblank_irq(self)
    cdef void set_hblank_irq(self, bint)
    cdef bint get_vcount_irq(self)
    cdef void set_vcount_irq(self, bint)
    cdef uint32_t get_vcount_trigger_value(self)
    cdef void set_vcount_trigger_value(self, uint32_t)

cdef class BackgroundControlRegister:
    cdef uint32_t reg

    cdef uint32_t get_priority(self)
    cdef uint32_t get_tile_set_block(self)
    cdef bint get_mosaic(self)
    cdef bint get_colour_256(self)
    cdef uint32_t get_tile_map_block(self)
    cdef bint get_wraparound(self)
    cdef uint32_t get_size(self)

cdef class WindowControlRegister:
    cdef uint32_t reg

    cdef bint display_layer(self, int)
    cdef bint get_enable_blending(self)
