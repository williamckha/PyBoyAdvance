from pyboy_advance.interrupt_controller import InterruptController
from pyboy_advance.memory.constants import IOAddress
from pyboy_advance.ppu.ppu import PPU
from pyboy_advance.utils import get_bit


class IO:
    def __init__(self, interrupt_controller: InterruptController, ppu: PPU):
        self.interrupt_controller = interrupt_controller
        self.ppu = ppu

    def read_32(self, address: int) -> int:
        lower_bits = self.read_16(address)
        upper_bits = self.read_16(address + 2)
        return (upper_bits << 8) | lower_bits

    def read_16(self, address: int) -> int:
        if address == IOAddress.REG_DISPCNT:
            return self.ppu.display_control.reg
        elif address == IOAddress.REG_DISPSTAT:
            return self.ppu.display_status.reg
        elif address == IOAddress.REG_VCOUNT:
            return self.ppu.vcount
        elif address == IOAddress.REG_IE:
            return self.interrupt_controller.interrupt_enable
        elif address == IOAddress.REG_IF:
            return self.interrupt_controller.interrupt_flags
        elif address == IOAddress.REG_IME:
            return self.interrupt_controller.interrupt_master_enable
        else:
            return 0

    def read_8(self, address: int) -> int:
        value = self.read_16(address & ~1)
        return (value >> ((address & 1) * 8)) & 0xFF

    def write_32(self, address: int, value: int):
        self.write_16(address, value & 0xFFFF)
        self.write_16(address + 2, (value >> 8) & 0xFFFF)

    def write_16(self, address: int, value: int):
        if address == IOAddress.REG_DISPCNT:
            self.ppu.display_control.reg = value
        elif address == IOAddress.REG_DISPSTAT:
            self.ppu.display_status.reg = value
        elif address == IOAddress.REG_VCOUNT:
            self.ppu.vcount = value
        elif address == IOAddress.REG_IE:
            self.interrupt_controller.interrupt_enable = value
        elif address == IOAddress.REG_IF:
            self.interrupt_controller.interrupt_flags = value
        elif address == IOAddress.REG_IME:
            self.interrupt_controller.interrupt_master_enable = value

    def write_8(self, address: int, value: int):
        aligned_address = address & ~1

        old_value = self.read_16(aligned_address)
        new_value = (
            (old_value & 0x00FF) | (value << 8)
            if get_bit(value, 0)
            else (old_value & 0xFF00) | value
        )

        self.write_16(aligned_address, new_value)
