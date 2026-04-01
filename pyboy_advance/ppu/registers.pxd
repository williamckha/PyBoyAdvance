from libc.stdint cimport uint32_t

from pyboy_advance.utils cimport get_bits, get_bit, set_bit

cdef class DisplayControlRegister:
    cdef uint32_t reg

    cdef int get_video_mode(self) noexcept
    cdef bint get_page_select(self) noexcept
    cdef bint get_hblank_interval_free(self) noexcept
    cdef bint get_obj_vram_dimension(self) noexcept
    cdef bint get_force_blank(self) noexcept
    cdef bint display_bg(self, int) noexcept
    cdef bint get_display_obj(self) noexcept
    cdef bint display_window(self, int) noexcept

cdef class DisplayStatusRegister:
    cdef uint32_t reg

    cdef bint get_vblank_status(self) noexcept
    cdef void set_vblank_status(self, bint) noexcept
    cdef bint get_hblank_status(self) noexcept
    cdef void set_hblank_status(self, bint) noexcept
    cdef bint get_vcount_trigger_status(self) noexcept
    cdef void set_vcount_trigger_status(self, bint) noexcept
    cdef bint get_vblank_irq(self) noexcept
    cdef void set_vblank_irq(self, bint) noexcept
    cdef bint get_hblank_irq(self) noexcept
    cdef void set_hblank_irq(self, bint) noexcept
    cdef bint get_vcount_irq(self) noexcept
    cdef void set_vcount_irq(self, bint) noexcept
    cdef uint32_t get_vcount_trigger_value(self) noexcept
    cdef void set_vcount_trigger_value(self, uint32_t) noexcept

cdef class BackgroundControlRegister:
    cdef uint32_t reg

    cdef uint32_t get_priority(self) noexcept
    cdef uint32_t get_tile_set_block(self) noexcept
    cdef bint get_mosaic(self) noexcept
    cdef bint get_colour_256(self) noexcept
    cdef uint32_t get_tile_map_block(self) noexcept
    cdef bint get_wraparound(self) noexcept
    cdef uint32_t get_size(self) noexcept

cdef class WindowControlRegister:
    cdef uint32_t reg

    cdef bint display_layer(self, int) noexcept
    cdef bint get_enable_blending(self) noexcept

cdef class BlendControlRegister:
    cdef uint32_t reg

    cdef bint blend_source(self, int) noexcept
    cdef bint blend_target(self, int) noexcept
    cdef int get_blend_mode(self) noexcept

cdef class BlendAlphaRegister:
    cdef uint32_t reg

    cdef uint32_t get_coefficient_source(self) noexcept
    cdef uint32_t get_coefficient_target(self) noexcept

cdef class BlendBrightnessRegister:
    cdef uint32_t reg

    cdef uint32_t get_brightness(self) noexcept
