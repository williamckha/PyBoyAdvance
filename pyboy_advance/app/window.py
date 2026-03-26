# ifndef CYTHON
from __future__ import annotations

from pyboy_advance.app.constants import WindowEvent
from pyboy_advance.ppu.constants import DISPLAY_WIDTH, DISPLAY_HEIGHT, COLOUR_SIZE
# endif

from ctypes import c_void_p

import sdl2.ext


# fmt: off
DEFAULT_KEY_DOWN_MAP = {
    sdl2.SDLK_a         : WindowEvent.PRESS_BUTTON_A,
    sdl2.SDLK_s         : WindowEvent.PRESS_BUTTON_B,
    sdl2.SDLK_BACKSPACE : WindowEvent.PRESS_BUTTON_SELECT,
    sdl2.SDLK_RETURN    : WindowEvent.PRESS_BUTTON_START,
    sdl2.SDLK_RIGHT     : WindowEvent.PRESS_DPAD_RIGHT,
    sdl2.SDLK_LEFT      : WindowEvent.PRESS_DPAD_LEFT,
    sdl2.SDLK_UP        : WindowEvent.PRESS_DPAD_UP,
    sdl2.SDLK_DOWN      : WindowEvent.PRESS_DPAD_DOWN,
    sdl2.SDLK_w         : WindowEvent.PRESS_SHOULDER_RIGHT,
    sdl2.SDLK_q         : WindowEvent.PRESS_SHOULDER_LEFT,
}

DEFAULT_KEY_UP_MAP = {
    sdl2.SDLK_a         : WindowEvent.RELEASE_BUTTON_A,
    sdl2.SDLK_s         : WindowEvent.RELEASE_BUTTON_B,
    sdl2.SDLK_BACKSPACE : WindowEvent.RELEASE_BUTTON_SELECT,
    sdl2.SDLK_RETURN    : WindowEvent.RELEASE_BUTTON_START,
    sdl2.SDLK_RIGHT     : WindowEvent.RELEASE_DPAD_RIGHT,
    sdl2.SDLK_LEFT      : WindowEvent.RELEASE_DPAD_LEFT,
    sdl2.SDLK_UP        : WindowEvent.RELEASE_DPAD_UP,
    sdl2.SDLK_DOWN      : WindowEvent.RELEASE_DPAD_DOWN,
    sdl2.SDLK_w         : WindowEvent.RELEASE_SHOULDER_RIGHT,
    sdl2.SDLK_q         : WindowEvent.RELEASE_SHOULDER_LEFT,
    sdl2.SDLK_ESCAPE    : WindowEvent.QUIT,
    sdl2.SDLK_F11       : WindowEvent.FULLSCREEN,
}
# fmt: on


class Window:
    def __init__(self):
        self._events = []
        self._key_down_map = DEFAULT_KEY_DOWN_MAP
        self._key_up_map = DEFAULT_KEY_UP_MAP
        self._window_scale = 3

    def __enter__(self):
        if sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_GAMECONTROLLER) < 0:
            raise ValueError(f"SDL_InitSubSystem failed: {sdl2.SDL_GetError().decode()}")

        self._sdl_window = sdl2.SDL_CreateWindow(
            b"PyBoy Advance",
            sdl2.SDL_WINDOWPOS_CENTERED,
            sdl2.SDL_WINDOWPOS_CENTERED,
            DISPLAY_WIDTH * self._window_scale,
            DISPLAY_HEIGHT * self._window_scale,
            sdl2.SDL_WINDOW_RESIZABLE,
        )

        self._sdl_renderer = sdl2.SDL_CreateRenderer(
            self._sdl_window, -1, sdl2.SDL_RENDERER_ACCELERATED
        )

        sdl2.SDL_RenderSetLogicalSize(self._sdl_renderer, DISPLAY_WIDTH, DISPLAY_HEIGHT)

        self._sdl_texture_buffer = sdl2.SDL_CreateTexture(
            self._sdl_renderer,
            sdl2.SDL_PIXELFORMAT_BGR555,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            DISPLAY_WIDTH,
            DISPLAY_HEIGHT,
        )

        sdl2.SDL_ShowWindow(self._sdl_window)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sdl2.SDL_DestroyWindow(self._sdl_window)
        sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_GAMECONTROLLER)

    @property
    def fullscreen(self) -> bool:
        flags = sdl2.SDL_GetWindowFlags(self._sdl_window)
        return flags & sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP

    @fullscreen.setter
    def fullscreen(self, value: bool):
        sdl2.SDL_SetWindowFullscreen(
            self._sdl_window,
            sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP if value else 0,
        )

    def get_events(self) -> list[WindowEvent]:
        self._events.clear()
        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_QUIT:
                self._events.append(WindowEvent.QUIT)
            elif event.type == sdl2.SDL_KEYDOWN:
                self._events.append(self._key_down_map.get(event.key.keysym.sym, WindowEvent.NONE))
            elif event.type == sdl2.SDL_KEYUP:
                self._events.append(self._key_up_map.get(event.key.keysym.sym, WindowEvent.NONE))
        return self._events

    def render(self, frame_buffer_ptr: c_void_p):
        sdl2.SDL_UpdateTexture(
            self._sdl_texture_buffer,
            None,
            frame_buffer_ptr,
            DISPLAY_WIDTH * COLOUR_SIZE,
        )
        sdl2.SDL_RenderClear(self._sdl_renderer)
        sdl2.SDL_RenderCopy(self._sdl_renderer, self._sdl_texture_buffer, None, None)
        sdl2.SDL_RenderPresent(self._sdl_renderer)
