# ifndef CYTHON
from __future__ import annotations

from pyboy_advance.ppu.constants import LayerType, WindowIndex, VideoMode, BlendMode
from pyboy_advance.utils import get_bits, get_bit, set_bit, bint
# endif


class DisplayControlRegister:
    def __init__(self):
        self.reg = 0

    @property
    def video_mode(self) -> VideoMode | int:
        return get_bits(self.reg, 0, 2)

    @property
    def page_select(self) -> bint:
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

    def display_bg(self, bg_num: int) -> bint:
        return get_bit(self.reg, 8 + bg_num)

    @property
    def display_obj(self) -> bint:
        return get_bit(self.reg, 12)

    def display_window(self, window: WindowIndex) -> bint:
        return get_bit(self.reg, 13 + window)


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
    def tile_set_block(self) -> int:
        return get_bits(self.reg, 2, 3)

    @property
    def mosaic(self) -> bint:
        return get_bit(self.reg, 6)

    @property
    def colour_256(self) -> bint:
        return get_bit(self.reg, 7)

    @property
    def tile_map_block(self) -> int:
        return get_bits(self.reg, 8, 12)

    @property
    def wraparound(self) -> bint:
        return get_bit(self.reg, 13)

    @property
    def size(self) -> int:
        return get_bits(self.reg, 14, 15)


class WindowControlRegister:
    def __init__(self):
        self.reg = 0

    def display_layer(self, layer_type: LayerType) -> bint:
        return get_bit(self.reg, layer_type)

    @property
    def enable_blending(self) -> bint:
        return get_bit(self.reg, 5)


class MosaicControlRegister:
    def __init__(self):
        self.reg = 0

    @property
    def stretch_bg_horizontal(self) -> int:
        return get_bits(self.reg, 0, 3)

    @property
    def stretch_bg_vertical(self) -> int:
        return get_bits(self.reg, 4, 7)

    @property
    def stretch_obj_horizontal(self) -> int:
        return get_bits(self.reg, 8, 11)

    @property
    def stretch_obj_vertical(self) -> int:
        return get_bits(self.reg, 12, 15)


class BlendControlRegister:
    def __init__(self):
        self.reg = 0

    def blend_source(self, layer_type: LayerType | int) -> bint:
        return get_bit(self.reg, layer_type)

    def blend_target(self, layer_type: LayerType | int) -> bint:
        return get_bit(self.reg, 8 + layer_type)

    @property
    def blend_mode(self) -> BlendMode | int:
        return get_bits(self.reg, 6, 7)


class BlendAlphaRegister:
    def __init__(self):
        self.reg = 0

    @property
    def coefficient_source(self) -> int:
        return get_bits(self.reg, 0, 4)

    @property
    def coefficient_target(self) -> int:
        return get_bits(self.reg, 8, 12)


class BlendBrightnessRegister:
    def __init__(self):
        self.reg = 0

    @property
    def amount(self) -> int:
        return get_bits(self.reg, 0, 4)
