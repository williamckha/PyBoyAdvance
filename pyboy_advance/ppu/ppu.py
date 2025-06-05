from array import array
from ctypes import c_void_p
from enum import IntEnum

from pyboy_advance.memory.constants import MemoryRegion
from pyboy_advance.scheduler import Scheduler
from pyboy_advance.utils import (
    get_bit,
    get_bits,
    set_bit,
    array_read_16,
    bint,
)

DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 160

HBLANK_PIXELS = 68
VBLANK_LINES = 68

DISPLAY_FULL_WIDTH = DISPLAY_WIDTH + HBLANK_PIXELS
DISPLAY_FULL_HEIGHT = DISPLAY_HEIGHT + VBLANK_LINES

CYCLES_PIXEL = 4
CYCLES_HDRAW = DISPLAY_WIDTH * CYCLES_PIXEL
CYCLES_HBLANK = HBLANK_PIXELS * CYCLES_PIXEL


class PPU:
    def __init__(self, scheduler: Scheduler):
        self.display_control = DisplayControlRegister()
        self.display_status = DisplayStatusRegister()
        self.vcount = 0

        self.palram = array("B", [0] * MemoryRegion.PALRAM_SIZE)
        self.vram = array("B", [0] * MemoryRegion.VRAM_SIZE)
        self.oam = array("B", [0] * MemoryRegion.OAM_SIZE)

        self.front_buffer = array("H", [0] * (DISPLAY_WIDTH * DISPLAY_HEIGHT))
        self.back_buffer = array("H", [0] * (DISPLAY_WIDTH * DISPLAY_HEIGHT))
        self.front_buffer_ptr = c_void_p(self.front_buffer.buffer_info()[0])
        self.back_buffer_ptr = c_void_p(self.front_buffer.buffer_info()[0])

        self.scheduler = scheduler
        self.scheduler.schedule(self.hblank_start, CYCLES_HDRAW)

    @property
    def frame_buffer_ptr(self) -> c_void_p:
        return self.front_buffer_ptr

    def render_scanline(self):
        video_mode = self.display_control.video_mode
        if video_mode == VideoMode.MODE_0:
            self.render_scanline_mode_0()
        elif video_mode == VideoMode.MODE_1:
            self.render_scanline_mode_1()
        elif video_mode == VideoMode.MODE_2:
            self.render_scanline_mode_2()
        elif video_mode == VideoMode.MODE_3:
            self.render_scanline_mode_3()
        elif video_mode == VideoMode.MODE_4:
            self.render_scanline_mode_4()
        elif video_mode == VideoMode.MODE_5:
            self.render_scanline_mode_5()

    def render_scanline_mode_0(self):
        pass

    def render_scanline_mode_1(self):
        pass

    def render_scanline_mode_2(self):
        pass

    def render_scanline_mode_3(self):
        pass

    def render_scanline_mode_4(self):
        page_offset = 0xA000 if self.display_control.display_frame_select else 0

        if self.display_control.display_bg_2:
            for x in range(DISPLAY_WIDTH):
                palette_index = self.vram[DISPLAY_WIDTH * self.vcount + page_offset + x]
                color = self.get_palette_color(palette_index)
                self.back_buffer[DISPLAY_WIDTH * self.vcount + x] = color

    def render_scanline_mode_5(self):
        pass

    def hblank_start(self):
        self.display_status.hblank_status = True

        if self.vcount < DISPLAY_HEIGHT:
            self.render_scanline()

        self.scheduler.schedule(self.hblank_end, CYCLES_HBLANK)

    def hblank_end(self):
        self.vcount += 1
        if self.vcount >= DISPLAY_FULL_HEIGHT:
            self.vcount = 0

        self.display_status.hblank_status = False
        self.display_status.vblank_status = self.vcount >= DISPLAY_HEIGHT

        if self.vcount == DISPLAY_HEIGHT:
            # Swap front and back buffers
            # (done at this point to avoid tearing, now that the back buffer is complete)
            self.front_buffer, self.back_buffer = self.back_buffer, self.front_buffer
            self.front_buffer_ptr, self.back_buffer_ptr = (
                self.back_buffer_ptr,
                self.front_buffer_ptr,
            )

        self.scheduler.schedule(self.hblank_start, CYCLES_HDRAW)

    def get_palette_color(self, index):
        color = array_read_16(self.palram, index * 2)
        return color & 0x7FFF


class VideoMode(IntEnum):
    MODE_0 = 0
    MODE_1 = 1
    MODE_2 = 2
    MODE_3 = 3
    MODE_4 = 4
    MODE_5 = 5

    @classmethod
    def _missing_(cls, value):
        if value == 6 or value == 7:
            return cls.MODE_5

    def is_bitmapped(self):
        return self in [VideoMode.MODE_3, VideoMode.MODE_4, VideoMode.MODE_5]


class DisplayControlRegister:
    def __init__(self):
        self.reg = 0

    @property
    def video_mode(self) -> VideoMode:
        return VideoMode(get_bits(self.reg, 0, 2))

    @property
    def display_frame_select(self) -> bint:
        return get_bit(self.reg, 4)

    @property
    def hblank_interval_free(self) -> bint:
        return get_bit(self.reg, 5)

    @property
    def obj_vram_dimension(self) -> bint:
        return get_bit(self.reg, 6)

    @property
    def force_blank(self) -> bint:
        return get_bit(self.reg, 7)

    @property
    def display_bg_0(self) -> bint:
        return get_bit(self.reg, 8)

    @property
    def display_bg_1(self) -> bint:
        return get_bit(self.reg, 9)

    @property
    def display_bg_2(self) -> bint:
        return get_bit(self.reg, 10)

    @property
    def display_bg_3(self) -> bint:
        return get_bit(self.reg, 11)

    @property
    def display_obj(self) -> bint:
        return get_bit(self.reg, 12)

    @property
    def display_window_0(self) -> bint:
        return get_bit(self.reg, 13)

    @property
    def display_window_1(self) -> bint:
        return get_bit(self.reg, 14)

    @property
    def display_obj_window(self) -> bint:
        return get_bit(self.reg, 15)


class DisplayStatusRegister:
    def __init__(self):
        self.reg = 0

    @property
    def vblank_status(self) -> bint:
        return get_bit(self.reg, 0)

    @vblank_status.setter
    def vblank_status(self, value: bint):
        self.reg = set_bit(self.reg, 0, value)

    @property
    def hblank_status(self) -> bint:
        return get_bit(self.reg, 1)

    @hblank_status.setter
    def hblank_status(self, value: bint):
        self.reg = set_bit(self.reg, 1, value)

    @property
    def vcount_trigger_status(self) -> bint:
        return get_bit(self.reg, 2)

    @vcount_trigger_status.setter
    def vcount_trigger_status(self, value: bint):
        self.reg = set_bit(self.reg, 2, value)

    @property
    def vblank_irq(self) -> bint:
        return get_bit(self.reg, 3)

    @vblank_irq.setter
    def vblank_irq(self, value: bint):
        self.reg = set_bit(self.reg, 3, value)

    @property
    def hblank_irq(self) -> bint:
        return get_bit(self.reg, 4)

    @hblank_irq.setter
    def hblank_irq(self, value: bint):
        self.reg = set_bit(self.reg, 4, value)

    @property
    def vcount_irq(self) -> bint:
        return get_bit(self.reg, 5)

    @vcount_irq.setter
    def vcount_irq(self, value: bint):
        self.reg = set_bit(self.reg, 5, value)

    @property
    def vcount_trigger_value(self) -> int:
        return get_bits(self.reg, 8, 15)

    @vcount_trigger_value.setter
    def vcount_trigger_value(self, value: int):
        self.reg = (self.reg & 0xFF) | (value << 8)
