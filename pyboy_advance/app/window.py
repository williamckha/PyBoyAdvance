from ctypes import c_void_p

import sdl2.ext

from pyboy_advance.ppu.ppu import DISPLAY_HEIGHT, DISPLAY_WIDTH


class Window:
    DEFAULT_WINDOW_SCALE = 2

    def __init__(self):
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_GAMECONTROLLER) < 0:
            raise ValueError(f"SDL_InitSubSystem failed: {sdl2.SDL_GetError().decode()}")

        self.sdl_window = sdl2.SDL_CreateWindow(
            b"PyBoy Advance",
            sdl2.SDL_WINDOWPOS_CENTERED,
            sdl2.SDL_WINDOWPOS_CENTERED,
            DISPLAY_WIDTH * Window.DEFAULT_WINDOW_SCALE,
            DISPLAY_HEIGHT * Window.DEFAULT_WINDOW_SCALE,
            sdl2.SDL_WINDOW_RESIZABLE,
        )

        self.sdl_renderer = sdl2.SDL_CreateRenderer(
            self.sdl_window, -1, sdl2.SDL_RENDERER_ACCELERATED
        )

        sdl2.SDL_RenderSetLogicalSize(self.sdl_renderer, DISPLAY_WIDTH, DISPLAY_HEIGHT)

        self.sdl_texture_buffer = sdl2.SDL_CreateTexture(
            self.sdl_renderer,
            sdl2.SDL_PIXELFORMAT_BGR555,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            DISPLAY_WIDTH,
            DISPLAY_HEIGHT,
        )

        sdl2.SDL_ShowWindow(self.sdl_window)

    def get_events(self):
        sdl2.ext.get_events()

    def render(self, frame_buffer_ptr: c_void_p):
        sdl2.SDL_UpdateTexture(self.sdl_texture_buffer, None, frame_buffer_ptr, DISPLAY_WIDTH * 2)
        sdl2.SDL_RenderClear(self.sdl_renderer)
        sdl2.SDL_RenderCopy(self.sdl_renderer, self.sdl_texture_buffer, None, None)
        sdl2.SDL_RenderPresent(self.sdl_renderer)
