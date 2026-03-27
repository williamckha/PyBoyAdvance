from pyboy_advance.app.constants cimport WindowEvent
from pyboy_advance.ppu.constants cimport DISPLAY_WIDTH, DISPLAY_HEIGHT, COLOUR_SIZE

cdef class Window:
    cdef list _events
    cdef dict _key_down_map
    cdef dict _key_up_map
    cdef int _window_scale
    cdef object _sdl_window
    cdef object _sdl_renderer
    cdef object _sdl_texture_buffer

    cdef bint get_fullscreen(self) noexcept
    cdef void set_fullscreen(self, bint) noexcept
    cdef list get_events(self) noexcept
    cdef void render(self, c_void_p) noexcept
