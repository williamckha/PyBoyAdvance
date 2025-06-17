from __future__ import annotations

from array import array
from ctypes import c_void_p
from enum import IntEnum

from pyboy_advance.interrupt_controller import InterruptController, Interrupt
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

SMALL_DISPLAY_WIDTH = 160
SMALL_DISPLAY_HEIGHT = 128

MAX_NUM_OBJECTS = 128
OAM_ENTRY_SIZE = 8

NUM_BACKGROUNDS = 4

NUM_PRIORITY_LEVELS = 4

TILE_WIDTH = TILE_HEIGHT = 8
TILE_SIZE = TILE_WIDTH * TILE_HEIGHT

COLOUR_SIZE = 2


class PPU:
    """
    Picture Processing Unit.
    """

    def __init__(self, scheduler: Scheduler, interrupt_controller: InterruptController):
        self.scheduler = scheduler
        self.interrupt_controller = interrupt_controller

        self.display_control = DisplayControlRegister()
        self.display_status = DisplayStatusRegister()
        self.vcount = 0

        self.bg_control = [BackgroundControlRegister() for _ in range(NUM_BACKGROUNDS)]
        self.bg_offset_h = [0] * NUM_BACKGROUNDS
        self.bg_offset_v = [0] * NUM_BACKGROUNDS

        self.palram = array("B", [0] * MemoryRegion.PALRAM_SIZE)
        self.vram = array("B", [0] * MemoryRegion.VRAM_SIZE)
        self.oam = array("B", [0] * MemoryRegion.OAM_SIZE)

        self.front_buffer = array("H", [0] * (DISPLAY_WIDTH * DISPLAY_HEIGHT))
        self.back_buffer = array("H", [0] * (DISPLAY_WIDTH * DISPLAY_HEIGHT))
        self.front_buffer_ptr = c_void_p(self.front_buffer.buffer_info()[0])
        self.back_buffer_ptr = c_void_p(self.front_buffer.buffer_info()[0])

        self.scheduler.schedule(self.hblank_start, CYCLES_HDRAW)

    @property
    def frame_buffer_ptr(self) -> c_void_p:
        return self.front_buffer_ptr

    def hblank_start(self):
        self.display_status.hblank_status = True

        if self.vcount < DISPLAY_HEIGHT:
            self.render_objects()
            self.render_background()

        if self.display_status.hblank_irq:
            self.interrupt_controller.signal(Interrupt.HBLANK)

        self.scheduler.schedule(self.hblank_end, CYCLES_HBLANK)

    def hblank_end(self):
        self.vcount += 1
        if self.vcount >= DISPLAY_FULL_HEIGHT:
            self.vcount = 0

        self.display_status.hblank_status = False
        self.display_status.vblank_status = self.vcount >= DISPLAY_HEIGHT
        self.display_status.vcount_trigger_status = (
            self.vcount == self.display_status.vcount_trigger_value
        )

        if self.vcount == DISPLAY_HEIGHT:
            # Swap front and back buffers
            # (done at this point to avoid tearing, now that the back buffer is complete)
            self.front_buffer, self.back_buffer = self.back_buffer, self.front_buffer
            self.front_buffer_ptr, self.back_buffer_ptr = (
                self.back_buffer_ptr,
                self.front_buffer_ptr,
            )

            if self.display_status.vblank_irq:
                self.interrupt_controller.signal(Interrupt.VBLANK)

        if self.display_status.vcount_irq and self.display_status.vcount_trigger_status:
            self.interrupt_controller.signal(Interrupt.VCOUNT)

        self.scheduler.schedule(self.hblank_start, CYCLES_HDRAW)

    def render_background(self):
        video_mode = self.display_control.video_mode

        if video_mode == VideoMode.MODE_0:
            for priority in range(NUM_PRIORITY_LEVELS):
                if self.display_control.display_bg_3 and self.bg_control[3].priority == priority:
                    self.render_background_text(bg_num=3)
                if self.display_control.display_bg_2 and self.bg_control[2].priority == priority:
                    self.render_background_text(bg_num=2)
                if self.display_control.display_bg_1 and self.bg_control[1].priority == priority:
                    self.render_background_text(bg_num=1)
                if self.display_control.display_bg_0 and self.bg_control[0].priority == priority:
                    self.render_background_text(bg_num=0)

        elif video_mode == VideoMode.MODE_1:
            for priority in range(NUM_PRIORITY_LEVELS):
                if self.display_control.display_bg_2 and self.bg_control[2].priority == priority:
                    self.render_background_affine(bg_num=2)
                if self.display_control.display_bg_1 and self.bg_control[1].priority == priority:
                    self.render_background_text(bg_num=1)
                if self.display_control.display_bg_0 and self.bg_control[0].priority == priority:
                    self.render_background_text(bg_num=0)

        elif video_mode == VideoMode.MODE_2:
            for priority in range(NUM_PRIORITY_LEVELS):
                if self.display_control.display_bg_3 and self.bg_control[3].priority == priority:
                    self.render_background_affine(bg_num=3)
                if self.display_control.display_bg_2 and self.bg_control[2].priority == priority:
                    self.render_background_affine(bg_num=2)

        elif video_mode == VideoMode.MODE_3:
            self.render_background_bitmap(paletted=False, small=False)

        elif video_mode == VideoMode.MODE_4:
            self.render_background_bitmap(paletted=True, small=False)

        elif video_mode == VideoMode.MODE_5:
            self.render_background_bitmap(paletted=False, small=True)

    def render_background_text(self, bg_num: int):
        bg_control = self.bg_control[bg_num]

        if bg_control.size == 0b00:
            tile_map_rows, tile_map_cols = 32, 32
        elif bg_control.size == 0b01:
            tile_map_rows, tile_map_cols = 32, 64
        elif bg_control.size == 0b10:
            tile_map_rows, tile_map_cols = 64, 32
        elif bg_control.size == 0b11:
            tile_map_rows, tile_map_cols = 64, 64
        else:
            raise ValueError

        rel_y = self.vcount + self.bg_offset_v[bg_num]
        tile_y = (rel_y // TILE_HEIGHT) % tile_map_rows
        pixel_y = rel_y % TILE_HEIGHT

        for x in range(DISPLAY_WIDTH):
            rel_x = x + self.bg_offset_h[bg_num]
            tile_x = (rel_x // TILE_WIDTH) % tile_map_cols
            pixel_x = rel_x % TILE_WIDTH

            tile_map_address = bg_control.tile_map_block
            tile_map_address += tile_y * tile_map_rows * 2
            tile_map_address += tile_x * 2

            tile_map_entry = array_read_16(self.vram, tile_map_address)
            tile_num = get_bits(tile_map_entry, 0, 9)
            tile_flip_h = get_bit(tile_map_entry, 10)
            tile_flip_v = get_bit(tile_map_entry, 11)
            palette_num = get_bits(tile_map_entry, 12, 15)

            pixel_x_flipped = TILE_WIDTH - pixel_x - 1 if tile_flip_h else pixel_x
            pixel_y_flipped = TILE_HEIGHT - pixel_y - 1 if tile_flip_v else pixel_y

            palette_index = self._get_palette_index(
                bg_control.tile_data_block,
                tile_num,
                pixel_x_flipped,
                pixel_y_flipped,
                bg_control.colour_256,
                palette_num,
            )

            colour = self._get_palette_colour(palette_index)
            self.back_buffer[DISPLAY_WIDTH * self.vcount + x] = colour

    def render_background_affine(self, bg_num: int):
        pass

    def render_background_bitmap(self, paletted, small):
        if self.display_control.display_bg_2:
            page_offset = 0xA000 if self.display_control.display_frame_select else 0

            display_width = SMALL_DISPLAY_WIDTH if small else DISPLAY_WIDTH
            display_height = SMALL_DISPLAY_HEIGHT if small else DISPLAY_HEIGHT

            if paletted:
                for x in range(display_width):
                    palette_index = self.vram[page_offset + display_width * self.vcount + x]
                    colour = self._get_palette_colour(palette_index)
                    self.back_buffer[DISPLAY_WIDTH * self.vcount + x] = colour
            else:
                for x in range(display_width):
                    vram_index = display_width * self.vcount + x
                    colour = array_read_16(self.vram, vram_index * COLOUR_SIZE)
                    self.back_buffer[DISPLAY_WIDTH * self.vcount + x] = colour

    def render_objects(self):
        for obj_index in range(MAX_NUM_OBJECTS - 1, -1, -1):
            obj_address = obj_index * OAM_ENTRY_SIZE
            obj = Object(
                array_read_16(self.oam, obj_address),
                array_read_16(self.oam, obj_address + 2),
                array_read_16(self.oam, obj_address + 4),
            )
            self.render_object(obj)

    def render_object(self, obj: Object):
        if obj.disabled:
            return

        if self.display_control.video_mode.bitmapped and obj.tile_index < 512:
            return

        obj_x, obj_y, (obj_w, obj_h) = obj.x, obj.y, obj.size
        obj_flip_h, obj_flip_v = obj.flip_horizontal, obj.flip_vertical

        if not (obj_y <= self.vcount < obj_y + obj_h):
            return

        tile_base_address = 0x10000 + obj.tile_index * 32
        tile_row_len = obj_w // 8 if self.display_control.obj_vram_dimension else 32

        offset_y = self.vcount - obj_y
        for offset_x in range(0, obj_w):
            rel_x = obj_w - offset_x - 1 if obj_flip_h else offset_x
            rel_y = obj_y - offset_y - 1 if obj_flip_v else offset_y

            tile_x = rel_x // TILE_WIDTH
            tile_y = rel_y // TILE_HEIGHT

            tile_index = tile_y * tile_row_len + tile_x

            pixel_x = rel_x % TILE_WIDTH
            pixel_y = rel_y % TILE_HEIGHT

            palette_index = self._get_palette_index(
                tile_base_address,
                tile_index,
                pixel_x,
                pixel_y,
                obj.colour_256,
                obj.palette_num,
            )

            colour = self._get_palette_colour(palette_index)
            self.back_buffer[DISPLAY_WIDTH * self.vcount + obj_x + offset_x] = colour

    def _get_palette_index(
        self,
        tile_base_address: int,
        tile_index: int,
        pixel_x: int,
        pixel_y: int,
        colour_256: bint,
        palette_num: int,
    ) -> int:
        if colour_256:
            # 256-colour object; one byte per pixel, one palette with 256 colours
            pixel_address = tile_base_address
            pixel_address += tile_index * TILE_SIZE + pixel_y * TILE_WIDTH + pixel_x
            palette_index = self.vram[pixel_address]
        else:
            # 16-colour object; each byte represents two pixels

            # Palette num selects one of 16 palettes, each palette having 16 colours
            palette_index = palette_num * 16

            # Lower 4 bits are for the left pixel and upper 4 bits are for the right pixel
            pixel_address = tile_base_address
            pixel_address += (tile_index * TILE_SIZE + pixel_y * TILE_WIDTH + pixel_x) // 2
            palette_index += (self.vram[pixel_address] >> ((pixel_x % 2) * 4)) & 0xF

        return palette_index

    def _get_palette_colour(self, palette_index: int) -> int:
        return array_read_16(self.palram, palette_index * COLOUR_SIZE)


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

    @property
    def bitmapped(self):
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


class BackgroundControlRegister:
    def __init__(self):
        self.reg = 0

    @property
    def priority(self) -> int:
        return get_bits(self.reg, 0, 1)

    @property
    def tile_data_base_block(self) -> int:
        return get_bits(self.reg, 2, 3)

    @property
    def tile_data_block(self) -> int:
        return self.tile_data_base_block * 0x4000

    @property
    def mosaic(self) -> bint:
        return get_bit(self.reg, 6)

    @property
    def colour_256(self) -> bint:
        return get_bit(self.reg, 7)

    @property
    def tile_map_base_block(self) -> int:
        return get_bits(self.reg, 8, 12)

    @property
    def tile_map_block(self) -> int:
        return self.tile_map_base_block * 0x800

    @property
    def wraparound(self) -> bint:
        return get_bit(self.reg, 13)

    @property
    def size(self) -> int:
        return get_bits(self.reg, 14, 15)


class ObjectMode(IntEnum):
    NORMAL = 0
    BLEND = 1
    WINDOW = 2


class ObjectShape(IntEnum):
    SQUARE = 0
    HORIZONTAL = 1
    VERTICAL = 2


class Object:
    """
    Corresponds to an OAM entry representing an object (moveable sprite).
    Each entry consist of three 16-bit attributes.
    """

    SIZES = [
        [(8, 8), (16, 16), (32, 32), (64, 64)],  # Square
        [(16, 8), (32, 8), (32, 16), (64, 32)],  # Horizontal
        [(8, 16), (8, 32), (16, 32), (32, 64)],  # Vertical
    ]

    def __init__(self, attr_0: int, attr_1: int, attr_2: int):
        self.attr_0 = attr_0
        self.attr_1 = attr_1
        self.attr_2 = attr_2

    @property
    def x(self) -> int:
        return get_bits(self.attr_1, 0, 7)

    @property
    def y(self) -> int:
        return get_bits(self.attr_0, 0, 7)

    @property
    def affine(self) -> bint:
        return get_bit(self.attr_0, 8)

    @property
    def double_size(self) -> bint:
        return get_bit(self.attr_0, 9)

    @property
    def disabled(self) -> bint:
        return get_bit(self.attr_0, 9) & ~self.affine

    @property
    def mode(self) -> ObjectMode:
        return ObjectMode(get_bits(self.attr_0, 10, 11))

    @property
    def mosaic(self) -> bint:
        return get_bit(self.attr_0, 12)

    @property
    def colour_256(self) -> bint:
        return get_bit(self.attr_0, 13)

    @property
    def shape(self) -> ObjectShape:
        return ObjectShape(get_bits(self.attr_0, 14, 15))

    @property
    def flip_horizontal(self) -> bint:
        return get_bit(self.attr_1, 12) & ~self.affine

    @property
    def flip_vertical(self) -> bint:
        return get_bit(self.attr_1, 13) & ~self.affine

    @property
    def size(self) -> tuple[int, int]:
        size = get_bits(self.attr_1, 14, 15)
        return Object.SIZES[self.shape][size]

    @property
    def tile_index(self) -> int:
        return get_bits(self.attr_2, 0, 9)

    @property
    def priority(self) -> int:
        return get_bits(self.attr_2, 10, 11)

    @property
    def palette_num(self) -> int:
        return get_bits(self.attr_2, 12, 15)
