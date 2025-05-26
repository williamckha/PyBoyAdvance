from array import array
from enum import Enum

from pyboy_advance.cpu.cpu import CPU
from pyboy_advance.memory.constants import MemoryRegion
from pyboy_advance.utils import get_bit


class MemoryAccess(Enum):
    NON_SEQUENTIAL = 0
    SEQUENTIAL = 1


class Memory:

    def __init__(self, cpu: CPU):
        self.cpu = cpu

        # General Internal Memory
        self.bios = array("B", [0] * MemoryRegion.BIOS_SIZE)
        self.ewram = array("B", [0] * MemoryRegion.EWRAM_SIZE)
        self.iwram = array("B", [0] * MemoryRegion.IWRAM_SIZE)

        # Internal Display Memory
        self.palram = array("B", [0] * MemoryRegion.PALRAM_SIZE)
        self.vram = array("B", [0] * MemoryRegion.VRAM_SIZE)
        self.oam = array("B", [0] * MemoryRegion.OAM_SIZE)

        # External Memory (Game Pak)
        self.rom = array("B", [0] * MemoryRegion.GAMEPAK_SIZE)

        # If the program counter is not in the BIOS region, reading
        # BIOS will return the most recently fetched BIOS opcode,
        # which is tracked by this variable
        self.bios_last_opcode = 0

    def read_32(self, address: int, access_type: MemoryAccess) -> int:
        self._add_cycles(address, access_type)
        return self._read_32_internal(address)

    def read_16(self, address: int, access_type: MemoryAccess) -> int:
        self._add_cycles(address, access_type)
        return self._read_16_internal(address)

    def read_8(self, address: int, access_type: MemoryAccess) -> int:
        self._add_cycles(address, access_type)
        return self._read_8_internal(address)

    def _read_32_internal(self, address: int) -> int:
        match address >> 24:
            case MemoryRegion.BIOS_REGION:
                if address <= MemoryRegion.BIOS_END:
                    if self.cpu.regs.pc <= MemoryRegion.BIOS_END:
                        self.bios_last_opcode = Memory._array_read_32(self.bios, address & MemoryRegion.BIOS_MASK)
                    return self.bios_last_opcode
                else:
                    raise ValueError("Invalid BIOS read")
            case MemoryRegion.EWRAM_REGION:
                return Memory._array_read_32(self.ewram, address & MemoryRegion.EWRAM_MASK)
            case MemoryRegion.IWRAM_REGION:
                return Memory._array_read_32(self.iwram, address & MemoryRegion.IWRAM_MASK)
            case MemoryRegion.IO_REGION:
                raise NotImplementedError
            case MemoryRegion.PALRAM_REGION:
                return Memory._array_read_32(self.palram, address & MemoryRegion.PALRAM_MASK)
            case MemoryRegion.VRAM_REGION:
                mask = (MemoryRegion.VRAM_MASK_1 if get_bit(address, 4) else MemoryRegion.VRAM_MASK_2)
                return Memory._array_read_32(self.vram, address & mask)
            case MemoryRegion.OAM_REGION:
                return Memory._array_read_32(self.oam, address & MemoryRegion.OAM_MASK)
            case region if MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
                return Memory._array_read_32(self.rom, address & MemoryRegion.GAMEPAK_MASK)
            case MemoryRegion.SRAM_REGION:
                raise NotImplementedError
            case _:
                raise ValueError

    def _read_16_internal(self, address: int) -> int:
        match address >> 24:
            case MemoryRegion.BIOS_REGION:
                if address <= MemoryRegion.BIOS_END:
                    if self.cpu.regs.pc <= MemoryRegion.BIOS_END:
                        return Memory._array_read_16(self.bios, address & MemoryRegion.BIOS_MASK)
                    return (self.bios_last_opcode >> ((address & 2) << 3)) & 0xFFFF
                else:
                    raise ValueError("Invalid BIOS read")
            case MemoryRegion.EWRAM_REGION:
                return Memory._array_read_16(self.ewram, address & MemoryRegion.EWRAM_MASK)
            case MemoryRegion.IWRAM_REGION:
                return Memory._array_read_16(self.iwram, address & MemoryRegion.IWRAM_MASK)
            case MemoryRegion.IO_REGION:
                raise NotImplementedError
            case MemoryRegion.PALRAM_REGION:
                return Memory._array_read_16(self.palram, address & MemoryRegion.PALRAM_MASK)
            case MemoryRegion.VRAM_REGION:
                mask = (MemoryRegion.VRAM_MASK_1 if get_bit(address, 4) else MemoryRegion.VRAM_MASK_2)
                return Memory._array_read_16(self.vram, address & mask)
            case MemoryRegion.OAM_REGION:
                return Memory._array_read_16(self.oam, address & MemoryRegion.OAM_MASK)
            case region if MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
                return Memory._array_read_16(self.rom, address & MemoryRegion.GAMEPAK_MASK)
            case MemoryRegion.SRAM_REGION:
                raise NotImplementedError
            case _:
                raise ValueError

    def _read_8_internal(self, address: int) -> int:
        match address >> 24:
            case MemoryRegion.BIOS_REGION:
                if address <= MemoryRegion.BIOS_END:
                    if self.cpu.regs.pc <= MemoryRegion.BIOS_END:
                        return self.bios[address & MemoryRegion.BIOS_MASK]
                    return (self.bios_last_opcode >> ((address & 3) << 3)) & 0xFF
                else:
                    raise ValueError("Invalid BIOS read")
            case MemoryRegion.EWRAM_REGION:
                return self.ewram[address & MemoryRegion.EWRAM_MASK]
            case MemoryRegion.IWRAM_REGION:
                return self.iwram[address & MemoryRegion.IWRAM_MASK]
            case MemoryRegion.IO_REGION:
                raise NotImplementedError
            case MemoryRegion.PALRAM_REGION:
                return self.palram[address & MemoryRegion.PALRAM_MASK]
            case MemoryRegion.VRAM_REGION:
                mask = (MemoryRegion.VRAM_MASK_1 if get_bit(address, 4) else MemoryRegion.VRAM_MASK_2)
                return self.vram[address & mask]
            case MemoryRegion.OAM_REGION:
                return self.oam[address & MemoryRegion.OAM_MASK]
            case region if MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
                return self.rom[address & MemoryRegion.GAMEPAK_MASK]
            case MemoryRegion.SRAM_REGION:
                raise NotImplementedError
            case _:
                raise ValueError

    @staticmethod
    def _array_read_32(arr: array, address: int) -> int:
        """Read a little-endian 32-bit value from an array of bytes"""
        b0 = arr[address]
        b1 = arr[address + 1]
        b2 = arr[address + 2]
        b3 = arr[address + 3]
        return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

    @staticmethod
    def _array_read_16(arr: array, address: int) -> int:
        """Read a little-endian 16-bit value from an array of bytes"""
        b0 = arr[address]
        b1 = arr[address + 1]
        return b0 | (b1 << 8)

    def _add_cycles(self, address: int, access_type: MemoryAccess):
        pass
