from __future__ import annotations

from ctypes import c_void_p
from enum import Enum, auto

import sdl2.ext

from pyboy_advance.ppu.constants import DISPLAY_WIDTH, DISPLAY_HEIGHT, COLOUR_SIZE


class Window:
    DEFAULT_WINDOW_SCALE = 2

    def __init__(self):
        self._events = []

    def __enter__(self):
        if sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_GAMECONTROLLER) < 0:
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

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sdl2.SDL_DestroyWindow(self.sdl_window)
        sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_GAMECONTROLLER)

    @property
    def fullscreen(self) -> bool:
        flags = sdl2.SDL_GetWindowFlags(self.sdl_window)
        return flags & sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP

    @fullscreen.setter
    def fullscreen(self, value: bool):
        sdl2.SDL_SetWindowFullscreen(
            self.sdl_window,
            sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP if value else 0,
        )

    def get_events(self) -> list[WindowEvent]:
        self._events.clear()
        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_QUIT:
                self._events.append(WindowEvent.QUIT)
            elif event.type == sdl2.SDL_KEYDOWN:
                self._events.append(KeyMapping.KEY_DOWN.get(event.key.keysym.sym, WindowEvent.NONE))
            elif event.type == sdl2.SDL_KEYUP:
                self._events.append(KeyMapping.KEY_UP.get(event.key.keysym.sym, WindowEvent.NONE))
        return self._events

    def render(self, frame_buffer_ptr: c_void_p):
        sdl2.SDL_UpdateTexture(
            self.sdl_texture_buffer,
            None,
            frame_buffer_ptr,
            DISPLAY_WIDTH * COLOUR_SIZE,
        )
        sdl2.SDL_RenderClear(self.sdl_renderer)
        sdl2.SDL_RenderCopy(self.sdl_renderer, self.sdl_texture_buffer, None, None)
        sdl2.SDL_RenderPresent(self.sdl_renderer)


class WindowEvent(Enum):
    # fmt: off
    NONE = auto()

    QUIT                    = auto()
    FULLSCREEN              = auto()

    PRESS_BUTTON_A          = auto()
    PRESS_BUTTON_B          = auto()
    PRESS_BUTTON_SELECT     = auto()
    PRESS_BUTTON_START      = auto()
    PRESS_DPAD_RIGHT        = auto()
    PRESS_DPAD_LEFT         = auto()
    PRESS_DPAD_UP           = auto()
    PRESS_DPAD_DOWN         = auto()
    PRESS_SHOULDER_RIGHT    = auto()
    PRESS_SHOULDER_LEFT     = auto()

    RELEASE_BUTTON_A        = auto()
    RELEASE_BUTTON_B        = auto()
    RELEASE_BUTTON_SELECT   = auto()
    RELEASE_BUTTON_START    = auto()
    RELEASE_DPAD_RIGHT      = auto()
    RELEASE_DPAD_LEFT       = auto()
    RELEASE_DPAD_UP         = auto()
    RELEASE_DPAD_DOWN       = auto()
    RELEASE_SHOULDER_RIGHT  = auto()
    RELEASE_SHOULDER_LEFT   = auto()
    # fmt: on


class KeyMapping:
    # fmt: off
    KEY_DOWN = {
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

    KEY_UP = {
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