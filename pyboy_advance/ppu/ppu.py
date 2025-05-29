from pyboy_advance.utils import get_bit, get_bits, set_bit

DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 160

VBLANK_LINES = 68


class PPU:
    def __init__(self):
        self.display_control = DisplayControlRegister()
        self.display_status = DisplayStatusRegister()
        self.vcount = 0

    def draw(self):
        self.vcount += 1
        if self.vcount >= DISPLAY_HEIGHT:
            self.display_status.vblank_status = True
        elif self.vcount >= DISPLAY_HEIGHT + VBLANK_LINES:
            self.vcount = 0
            self.display_status.vblank_status = False


class DisplayControlRegister:

    def __init__(self):
        self.reg = 0


class DisplayStatusRegister:

    def __init__(self):
        self.reg = 0

    @property
    def vblank_status(self) -> bool:
        return get_bit(self.reg, 0)

    @vblank_status.setter
    def vblank_status(self, value: bool):
        self.reg = set_bit(self.reg, 0, value)

    @property
    def hblank_status(self) -> bool:
        return get_bit(self.reg, 1)

    @hblank_status.setter
    def hblank_status(self, value: bool):
        self.reg = set_bit(self.reg, 1, value)

    @property
    def vcount_trigger_status(self) -> bool:
        return get_bit(self.reg, 2)

    @vcount_trigger_status.setter
    def vcount_trigger_status(self, value: bool):
        self.reg = set_bit(self.reg, 2, value)

    @property
    def vblank_irq(self) -> bool:
        return get_bit(self.reg, 3)

    @vblank_irq.setter
    def vblank_irq(self, value: bool):
        self.reg = set_bit(self.reg, 3, value)

    @property
    def hblank_irq(self) -> bool:
        return get_bit(self.reg, 4)

    @hblank_irq.setter
    def hblank_irq(self, value: bool):
        self.reg = set_bit(self.reg, 4, value)

    @property
    def vcount_irq(self) -> bool:
        return get_bit(self.reg, 5)

    @vcount_irq.setter
    def vcount_irq(self, value: bool):
        self.reg = set_bit(self.reg, 5, value)

    @property
    def vcount_trigger_value(self) -> int:
        return get_bits(self.reg, 8, 15)

    @vcount_trigger_value.setter
    def vcount_trigger_value(self, value: int):
        self.reg = (self.reg & 0xFF) | (value << 8)
