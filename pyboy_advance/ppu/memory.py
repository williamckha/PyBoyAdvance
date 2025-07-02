from array import array

from pyboy_advance.memory.constants import MemoryRegion
from pyboy_advance.ppu.registers import DisplayControlRegister
from pyboy_advance.utils import (
    array_read_32,
    array_read_16,
    get_bit,
    array_write_32,
    array_write_16,
)


class VideoMemory:
    def __init__(self, display_control: DisplayControlRegister):
        self.display_control = display_control

        self.palram = array("B", [0] * MemoryRegion.PALRAM_SIZE)
        self.vram = array("B", [0] * MemoryRegion.VRAM_SIZE)
        self.oam = array("B", [0] * MemoryRegion.OAM_SIZE)

    def read_32_palram(self, address: int) -> int:
        return array_read_32(self.palram, address & MemoryRegion.PALRAM_MASK)

    def read_32_vram(self, address: int) -> int:
        mask = self._get_vram_address_mask(address)
        return array_read_32(self.vram, address & mask)

    def read_32_oam(self, address: int) -> int:
        return array_read_32(self.oam, address & MemoryRegion.OAM_MASK)

    def read_16_palram(self, address: int) -> int:
        return array_read_16(self.palram, address & MemoryRegion.PALRAM_MASK)

    def read_16_vram(self, address: int) -> int:
        mask = self._get_vram_address_mask(address)
        return array_read_16(self.vram, address & mask)

    def read_16_oam(self, address: int) -> int:
        return array_read_16(self.oam, address & MemoryRegion.OAM_MASK)

    def read_8_palram(self, address: int) -> int:
        return self.palram[address & MemoryRegion.PALRAM_MASK]

    def read_8_vram(self, address: int) -> int:
        mask = self._get_vram_address_mask(address)
        return self.vram[address & mask]

    def read_8_oam(self, address: int) -> int:
        return self.oam[address & MemoryRegion.OAM_MASK]

    def write_32_palram(self, address: int, value: int):
        array_write_32(self.palram, address & MemoryRegion.PALRAM_MASK, value)

    def write_32_vram(self, address: int, value: int):
        mask = self._get_vram_address_mask(address)
        array_write_32(self.vram, address & mask, value)

    def write_32_oam(self, address: int, value: int):
        array_write_32(self.oam, address & MemoryRegion.OAM_MASK, value)

    def write_16_palram(self, address: int, value: int):
        array_write_16(self.palram, address & MemoryRegion.PALRAM_MASK, value)

    def write_16_vram(self, address: int, value: int):
        mask = self._get_vram_address_mask(address)
        array_write_16(self.vram, address & mask, value)

    def write_16_oam(self, address: int, value: int):
        array_write_16(self.oam, address & MemoryRegion.OAM_MASK, value)

    def write_8_palram(self, address: int, value: int):
        # Writing a byte to PALRAM writes the value to both the upper and lower 8-bits
        # of the addressed halfword
        address = address & ~0b1  # Align address to 2-byte boundary
        self.palram[address & MemoryRegion.PALRAM_MASK] = value
        self.palram[(address + 1) & MemoryRegion.PALRAM_MASK] = value

    def write_8_vram(self, address: int, value: int):
        # VRAM is split into BG and OBJ regions.
        # Size of the BG region changes depending on whether we are in bitmap mode
        video_mode = self.display_control.video_mode
        bg_region_end = 0x14000 if video_mode.bitmapped else 0x10000

        # Ignore attempts to write a byte into OBJ, but allow writes into BG
        if address & 0x1FFFF < bg_region_end:
            # Writing a byte to BG writes the value to both the upper and lower 8-bits
            # of the addressed halfword
            address = address & ~0b1  # Align address to 2-byte boundary
            mask_1 = self._get_vram_address_mask(address)
            mask_2 = self._get_vram_address_mask(address + 1)
            self.vram[address & mask_1] = value
            self.vram[(address + 1) & mask_2] = value

    @staticmethod
    def _get_vram_address_mask(address: int):
        """
        Get the appropriate mask for the given VRAM address.

        GBA VRAM is 96 KB (64K + 32K) but is mirrored in 128 KB steps
        (64K + 32K + 32K, the two 32K blocks being mirrors of each other).

        Hence, if the address is in the mirrored upper region (bit 16 set), we use
        VRAM_MASK_1 to wrap it back into valid VRAM space. Otherwise, we use VRAM_MASK_2.
        """
        return MemoryRegion.VRAM_MASK_1 if get_bit(address, 16) else MemoryRegion.VRAM_MASK_2