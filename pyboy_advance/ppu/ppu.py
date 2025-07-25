from __future__ import annotations

from array import array
from ctypes import c_void_p

from pyboy_advance.interrupt_controller import InterruptController, Interrupt
from pyboy_advance.ppu.constants import *
from pyboy_advance.ppu.memory import VideoMemory
from pyboy_advance.ppu.registers import (
    VideoMode,
    DisplayControlRegister,
    DisplayStatusRegister,
    BackgroundControlRegister,
    WindowControlRegister,
)
from pyboy_advance.scheduler import Scheduler, EventTrigger
from pyboy_advance.utils import (
    get_bit,
    get_bits,
    bint,
    interpret_signed_9,
)


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

        self.window_v_min = [0] * NUM_PRIMARY_WINDOWS
        self.window_v_max = [0] * NUM_PRIMARY_WINDOWS
        self.window_h_min = [0] * NUM_PRIMARY_WINDOWS
        self.window_h_max = [0] * NUM_PRIMARY_WINDOWS

        self.window_control = {
            WindowIndex.WIN_0: WindowControlRegister(),
            WindowIndex.WIN_1: WindowControlRegister(),
            WindowIndex.WIN_OBJ: WindowControlRegister(),
            WindowIndex.WIN_OUT: WindowControlRegister(),
        }

        self.window_mask = {
            WindowIndex.WIN_0: array("H", [0] * DISPLAY_WIDTH),
            WindowIndex.WIN_1: array("H", [0] * DISPLAY_WIDTH),
            WindowIndex.WIN_OBJ: array("H", [0] * DISPLAY_WIDTH),
        }

        self.memory = VideoMemory(self.display_control)

        self.bg_scanline = [array("H", [0] * DISPLAY_WIDTH) for _ in range(NUM_BACKGROUNDS)]
        self.obj_scanline = [array("H", [0] * DISPLAY_WIDTH) for _ in range(NUM_PRIORITIES)]
        self.scanline = array("H", [0] * DISPLAY_WIDTH)

        self.front_buffer = array("H", [0] * (DISPLAY_WIDTH * DISPLAY_HEIGHT))
        self.back_buffer = array("H", [0] * (DISPLAY_WIDTH * DISPLAY_HEIGHT))
        self.front_buffer_ptr = c_void_p(self.front_buffer.buffer_info()[0])
        self.back_buffer_ptr = c_void_p(self.back_buffer.buffer_info()[0])

        self.scheduler.schedule(self.hblank_start, CYCLES_HDRAW)

    @property
    def frame_buffer_ptr(self) -> c_void_p:
        return self.front_buffer_ptr

    def hblank_start(self):
        self.display_status.hblank_status = True

        if self.vcount < DISPLAY_HEIGHT:
            self._init_layers()
            self._calc_window_masks()

            if not self.display_control.force_blank:
                self._render_backgrounds()
                self._render_objects()

            self._merge_layers()

            self.scheduler.trigger(EventTrigger.HBLANK)

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

            self.scheduler.trigger(EventTrigger.VBLANK)

        if self.display_status.vcount_irq and self.display_status.vcount_trigger_status:
            self.interrupt_controller.signal(Interrupt.VCOUNT)

        self.scheduler.schedule(self.hblank_start, CYCLES_HDRAW)

    def _init_layers(self):
        backdrop_colour = 0 if self.display_control.force_blank else self.memory.read_16_palram(0)
        for x in range(DISPLAY_WIDTH):
            self.scanline[x] = backdrop_colour

        for scanline in self.bg_scanline:
            for x in range(DISPLAY_WIDTH):
                scanline[x] = TRANSPARENT_COLOUR

        for scanline in self.obj_scanline:
            for x in range(DISPLAY_WIDTH):
                scanline[x] = TRANSPARENT_COLOUR

    def _render_backgrounds(self):
        video_mode = self.display_control.video_mode

        if video_mode == VideoMode.MODE_0:
            for bg_num in range(NUM_BACKGROUNDS):
                self._render_background_text(bg_num)

        elif video_mode == VideoMode.MODE_1:
            self._render_background_affine(bg_num=2)
            self._render_background_text(bg_num=1)
            self._render_background_text(bg_num=0)

        elif video_mode == VideoMode.MODE_2:
            self._render_background_affine(bg_num=3)
            self._render_background_affine(bg_num=2)

        elif video_mode == VideoMode.MODE_3:
            self._render_background_bitmap(paletted=False, small=False)

        elif video_mode == VideoMode.MODE_4:
            self._render_background_bitmap(paletted=True, small=False)

        elif video_mode == VideoMode.MODE_5:
            self._render_background_bitmap(paletted=False, small=True)

    def _render_background_text(self, bg_num: int):
        if not self.display_control.display_bg(bg_num):
            return

        bg_control = self.bg_control[bg_num]

        rel_y = self.vcount + self.bg_offset_v[bg_num]
        tile_y = rel_y // TILE_HEIGHT
        pixel_y = rel_y % TILE_HEIGHT

        for x in range(DISPLAY_WIDTH):
            rel_x = x + self.bg_offset_h[bg_num]
            tile_x = rel_x // TILE_WIDTH
            pixel_x = rel_x % TILE_WIDTH

            # Larger size backgrounds are accessed as (up to) 4 separate maps
            # that are laid out as contiguous blocks in VRAM, pictured below.
            # (each tile map block is 32 x 32 tiles in size)
            #
            # +-----------+-----------+-----------+-----------+
            # |  32 x 32  |  64 x 32  |  32 x 64  |  64 x 64  |
            # +-----------+-----------+-----------+-----------+
            # |    [0]    |   [0][1]  |    [0]    |   [0][1]  |
            # |           |           |    [1]    |   [2][3]  |
            # +-----------+-----------+-----------+-----------+
            #
            # Hence, we must first find the tile map block we are currently in
            # and then find the tile map entry inside that block.

            tile_map_block = bg_control.tile_map_block
            if bg_control.size == 0b01:  # 64 x 32
                if tile_x & TILE_MAP_BLOCK_WIDTH:
                    tile_map_block += 1
            elif bg_control.size == 0b10:  # 32 x 64
                if tile_y & TILE_MAP_BLOCK_HEIGHT:
                    tile_map_block += 1
            elif bg_control.size == 0b11:  # 64 x 64
                if tile_x & TILE_MAP_BLOCK_WIDTH:
                    tile_map_block += 1
                if tile_y & TILE_MAP_BLOCK_HEIGHT:
                    tile_map_block += 2

            tile_map_entry_address = (tile_y % TILE_MAP_BLOCK_HEIGHT) * TILE_MAP_BLOCK_WIDTH
            tile_map_entry_address += tile_x % TILE_MAP_BLOCK_WIDTH
            tile_map_entry_address *= TILE_MAP_ENTRY_SIZE
            tile_map_entry_address += tile_map_block * TILE_MAP_BLOCK_SIZE

            tile_map_entry = self.memory.read_16_vram(tile_map_entry_address)
            tile_num = get_bits(tile_map_entry, 0, 9)
            tile_flip_h = get_bit(tile_map_entry, 10)
            tile_flip_v = get_bit(tile_map_entry, 11)
            palette_num = get_bits(tile_map_entry, 12, 15)

            pixel_x_flipped = TILE_WIDTH - pixel_x - 1 if tile_flip_h else pixel_x
            pixel_y_flipped = TILE_HEIGHT - pixel_y - 1 if tile_flip_v else pixel_y

            palette_index = self._get_palette_index(
                bg_control.tile_set_block * TILE_SET_BLOCK_SIZE,
                tile_num,
                pixel_x_flipped,
                pixel_y_flipped,
                bg_control.colour_256,
                palette_num,
            )

            if palette_index:
                colour = self.memory.read_16_palram(palette_index * COLOUR_SIZE)
                self.bg_scanline[bg_num][x] = colour

    def _render_background_affine(self, bg_num: int):
        if not self.display_control.display_bg(bg_num):
            return

    def _render_background_bitmap(self, paletted, small):
        if not self.display_control.display_bg(2):
            return

        page_offset = VRAM_PAGE_OFFSET if self.display_control.page_select else 0

        display_width = SMALL_DISPLAY_WIDTH if small else DISPLAY_WIDTH
        display_height = SMALL_DISPLAY_HEIGHT if small else DISPLAY_HEIGHT

        if paletted:
            for x in range(display_width):
                palette_index = self.memory.read_8_vram(
                    page_offset + display_width * self.vcount + x
                )
                if palette_index:
                    colour = self.memory.read_16_palram(palette_index * COLOUR_SIZE)
                    self.bg_scanline[2][x] = colour
        else:
            for x in range(display_width):
                vram_index = display_width * self.vcount + x
                colour = self.memory.read_16_vram(vram_index * COLOUR_SIZE)
                self.bg_scanline[2][x] = colour

    def _render_objects(self):
        if not self.display_control.display_obj:
            return

        for obj_index in range(MAX_NUM_OBJECTS - 1, -1, -1):
            obj_address = obj_index * OAM_ENTRY_SIZE
            self._render_object(
                Object(
                    self.memory.read_16_oam(obj_address),
                    self.memory.read_16_oam(obj_address + 2),
                    self.memory.read_16_oam(obj_address + 4),
                )
            )

    def _render_object(self, obj: Object):
        if obj.disabled:
            return

        # Because the BG section of VRAM gets extended in bitmapped modes (hence
        # making the OBJ section smaller), attempts to use tiles 0-511 are ignored
        if self.display_control.video_mode.bitmapped and obj.tile_index < 512:
            return

        obj_x = interpret_signed_9(obj.x)
        obj_y = obj.y
        obj_w, obj_h = obj.size
        obj_flip_h, obj_flip_v = obj.flip_horizontal, obj.flip_vertical

        if obj_y + obj_h > 256:
            obj_y -= 256

        if self.vcount < obj_y or self.vcount >= obj_y + obj_h:
            return

        tile_row_len = obj_w // TILE_WIDTH if self.display_control.obj_vram_dimension else 32

        offset_y = self.vcount - obj_y
        rel_y = obj_y - offset_y - 1 if obj_flip_v else offset_y

        for offset_x in range(0, obj_w):
            win_x = obj_x + offset_x
            if win_x < 0 or win_x >= DISPLAY_WIDTH:
                continue

            rel_x = obj_w - offset_x - 1 if obj_flip_h else offset_x

            tile_x = rel_x // TILE_WIDTH
            tile_y = rel_y // TILE_HEIGHT
            tile_index = obj.tile_index + tile_y * tile_row_len + tile_x

            pixel_x = rel_x % TILE_WIDTH
            pixel_y = rel_y % TILE_HEIGHT

            palette_index = self._get_palette_index(
                OBJ_TILE_SET_OFFSET,
                tile_index,
                pixel_x,
                pixel_y,
                obj.colour_256,
                obj.palette_num,
            )

            if palette_index:
                if obj.mode == ObjectMode.WINDOW:
                    self.window_mask[WindowIndex.WIN_OBJ][win_x] = 1
                else:
                    colour = self.memory.read_16_palram(
                        OBJ_PALETTE_OFFSET + palette_index * COLOUR_SIZE
                    )
                    self.obj_scanline[obj.priority][win_x] = colour

    def _merge_layers(self):
        for priority in range(NUM_PRIORITIES - 1, -1, -1):
            for bg_num in range(NUM_BACKGROUNDS - 1, -1, -1):
                if (
                    self.display_control.display_bg(bg_num)
                    and self.bg_control[bg_num].priority == priority
                ):
                    self._merge_layer(self.bg_scanline[bg_num], LayerType(bg_num))

            if self.display_control.display_obj:
                self._merge_layer(self.obj_scanline[priority], LayerType.OBJ)

        for x in range(DISPLAY_WIDTH):
            self.back_buffer[DISPLAY_WIDTH * self.vcount + x] = self.scanline[x]

    def _merge_layer(self, scanline, layer_type: LayerType):
        windowing_enabled = (
            self.display_control.display_window(WindowIndex.WIN_0)
            or self.display_control.display_window(WindowIndex.WIN_1)
            or self.display_control.display_window(WindowIndex.WIN_OBJ)
        )

        for x in range(DISPLAY_WIDTH):
            if windowing_enabled:
                window_control = self._get_window_for_pixel(x)
                if not window_control.display_layer(layer_type):
                    continue

            colour = scanline[x]
            if colour != TRANSPARENT_COLOUR:
                self.scanline[x] = colour

    def _calc_window_masks(self):
        for window in (WindowIndex.WIN_0, WindowIndex.WIN_1):
            window_mask = self.window_mask[window]

            h_min = self.window_h_min[window]
            h_max = self.window_h_max[window]
            v_min = self.window_v_min[window]
            v_max = self.window_v_max[window]

            inside_v_bounds = (
                v_min <= self.vcount < v_max
                if v_min <= v_max
                else (self.vcount < v_max or self.vcount >= v_min)
            )

            if not self.display_control.display_window(window) or not inside_v_bounds:
                for x in range(DISPLAY_WIDTH):
                    window_mask[x] = 0
            else:
                if h_min <= h_max:
                    for x in range(DISPLAY_WIDTH):
                        window_mask[x] = h_min <= x < h_max
                else:
                    for x in range(DISPLAY_WIDTH):
                        window_mask[x] = x < h_max or x >= h_min

        for x in range(DISPLAY_WIDTH):
            self.window_mask[WindowIndex.WIN_OBJ][x] = 0

    def _get_window_for_pixel(self, x):
        if self.window_mask[WindowIndex.WIN_0][x]:
            return self.window_control[WindowIndex.WIN_0]
        elif self.window_mask[WindowIndex.WIN_1][x]:
            return self.window_control[WindowIndex.WIN_1]
        elif self.window_mask[WindowIndex.WIN_OBJ][x]:
            return self.window_control[WindowIndex.WIN_OBJ]
        else:
            return self.window_control[WindowIndex.WIN_OUT]

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
            palette_index = self.memory.read_8_vram(pixel_address)
        else:
            # 16-colour object; each byte represents two pixels

            # Lower 4 bits are for the left pixel and upper 4 bits are for the right pixel
            pixel_address = tile_base_address
            pixel_address += (tile_index * TILE_SIZE + pixel_y * TILE_WIDTH + pixel_x) // 2
            palette_index = (self.memory.read_8_vram(pixel_address) >> ((pixel_x % 2) * 4)) & 0xF

            if palette_index == 0:
                return 0

            # Palette num selects one of 16 palettes, each palette having 16 colours
            palette_index += palette_num * 16

        return palette_index


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
    Each entry consists of three 16-bit attributes.
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
        return get_bits(self.attr_1, 0, 8)

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
