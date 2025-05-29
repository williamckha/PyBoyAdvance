from __future__ import annotations

from array import array
from enum import Enum
from typing import TYPE_CHECKING

from pyboy_advance.memory.constants import MemoryRegion
from pyboy_advance.memory.gamepak import GamePak
from pyboy_advance.utils import get_bit, array_read_16, array_read_32, array_write_32, array_write_16, ror_32, \
    extend_sign_16, extend_sign_8

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


class MemoryAccess(Enum):
    NON_SEQUENTIAL = 0
    SEQUENTIAL = 1


class Memory:

    def __init__(self, gamepak: GamePak):
        self.cpu: CPU | None = None

        # General Internal Memory
        self.bios = array("B", [0] * MemoryRegion.BIOS_SIZE)
        self.ewram = array("B", [0] * MemoryRegion.EWRAM_SIZE)
        self.iwram = array("B", [0] * MemoryRegion.IWRAM_SIZE)

        # Internal Display Memory
        self.palram = array("B", [0] * MemoryRegion.PALRAM_SIZE)
        self.vram = array("B", [0] * MemoryRegion.VRAM_SIZE)
        self.oam = array("B", [0] * MemoryRegion.OAM_SIZE)

        # External Memory (Game Pak)
        self.gamepak = gamepak

        # If the program counter is not in the BIOS region, reading
        # BIOS will return the most recently fetched BIOS opcode,
        # which is tracked by this variable
        self.bios_last_opcode = 0

    def connect_cpu(self, cpu: CPU):
        self.cpu = cpu

    def read_32(self, address: int, access_type: MemoryAccess) -> int:
        self._add_cycles(address, access_type)
        return self._read_32_internal(address)

    def read_32_ror(self, address: int, access_type: MemoryAccess) -> int:
        value = self.read_32(address, access_type)
        rotate = (address & 0b11) * 8
        return ror_32(value, rotate)

    def read_16(self, address: int, access_type: MemoryAccess) -> int:
        self._add_cycles(address, access_type)
        return self._read_16_internal(address)

    def read_16_signed(self, address: int, access_type: MemoryAccess) -> int:
        value = self.read_16(address, access_type)
        return extend_sign_8(value) if get_bit(address, 0) else extend_sign_16(value)

    def read_16_ror(self, address: int, access_type: MemoryAccess) -> int:
        value = self.read_16(address, access_type)
        rotate = (address & 0b1) * 8
        return ror_32(value, rotate)

    def read_8(self, address: int, access_type: MemoryAccess) -> int:
        self._add_cycles(address, access_type)
        return self._read_8_internal(address)

    def read_8_signed(self, address: int, access_type: MemoryAccess) -> int:
        value = self.read_8(address, access_type)
        return extend_sign_8(value)

    def write_32(self, address: int, value: int, access_type: MemoryAccess):
        self._add_cycles(address, access_type)
        self._write_32_internal(address, value)

    def write_16(self, address: int, value: int, access_type: MemoryAccess):
        self._add_cycles(address, access_type)
        self._write_16_internal(address, value)

    def write_8(self, address: int, value: int, access_type: MemoryAccess):
        self._add_cycles(address, access_type)
        self._write_8_internal(address, value)

    def _read_32_internal(self, address: int) -> int:
        match address >> 24:
            case MemoryRegion.BIOS_REGION:
                if address <= MemoryRegion.BIOS_END:
                    if not self.cpu or self.cpu.regs.pc <= MemoryRegion.BIOS_END:
                        self.bios_last_opcode = array_read_32(self.bios, address & MemoryRegion.BIOS_MASK)
                    return self.bios_last_opcode
                else:
                    raise ValueError(f"Invalid BIOS read_32 at address {address:#010x}")
            case MemoryRegion.EWRAM_REGION:
                return array_read_32(self.ewram, address & MemoryRegion.EWRAM_MASK)
            case MemoryRegion.IWRAM_REGION:
                return array_read_32(self.iwram, address & MemoryRegion.IWRAM_MASK)
            case MemoryRegion.IO_REGION:
                # Not implemented, ignore instead of error
                return 0
            case MemoryRegion.PALRAM_REGION:
                return array_read_32(self.palram, address & MemoryRegion.PALRAM_MASK)
            case MemoryRegion.VRAM_REGION:
                mask = (MemoryRegion.VRAM_MASK_1 if get_bit(address, 4) else MemoryRegion.VRAM_MASK_2)
                return array_read_32(self.vram, address & mask)
            case MemoryRegion.OAM_REGION:
                return array_read_32(self.oam, address & MemoryRegion.OAM_MASK)
            case region if MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
                return self.gamepak.read_32(address)
            case MemoryRegion.SRAM_REGION:
                return self.gamepak.read_32(address)
            case _:
                raise NotImplementedError(f"Attempt to read from unused memory: {address:#010x}")

    def _read_16_internal(self, address: int) -> int:
        match address >> 24:
            case MemoryRegion.BIOS_REGION:
                if address <= MemoryRegion.BIOS_END:
                    if not self.cpu or self.cpu.regs.pc <= MemoryRegion.BIOS_END:
                        return array_read_16(self.bios, address & MemoryRegion.BIOS_MASK)
                    return (self.bios_last_opcode >> ((address & 2) << 3)) & 0xFFFF
                else:
                    raise ValueError(f"Invalid BIOS read_16 at address {address:#010x}")
            case MemoryRegion.EWRAM_REGION:
                return array_read_16(self.ewram, address & MemoryRegion.EWRAM_MASK)
            case MemoryRegion.IWRAM_REGION:
                return array_read_16(self.iwram, address & MemoryRegion.IWRAM_MASK)
            case MemoryRegion.IO_REGION:
                # Not implemented, ignore instead of error
                return 0
            case MemoryRegion.PALRAM_REGION:
                return array_read_16(self.palram, address & MemoryRegion.PALRAM_MASK)
            case MemoryRegion.VRAM_REGION:
                mask = (MemoryRegion.VRAM_MASK_1 if get_bit(address, 4) else MemoryRegion.VRAM_MASK_2)
                return array_read_16(self.vram, address & mask)
            case MemoryRegion.OAM_REGION:
                return array_read_16(self.oam, address & MemoryRegion.OAM_MASK)
            case region if MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
                return self.gamepak.read_16(address)
            case MemoryRegion.SRAM_REGION:
                return self.gamepak.read_16(address)
            case _:
                raise NotImplementedError(f"Attempt to read from unused memory: {address:#010x}")

    def _read_8_internal(self, address: int) -> int:
        match address >> 24:
            case MemoryRegion.BIOS_REGION:
                if address <= MemoryRegion.BIOS_END:
                    if not self.cpu or self.cpu.regs.pc <= MemoryRegion.BIOS_END:
                        return self.bios[address & MemoryRegion.BIOS_MASK]
                    return (self.bios_last_opcode >> ((address & 3) << 3)) & 0xFF
                else:
                    raise ValueError(f"Invalid BIOS read_8 at address {address:#010x}")
            case MemoryRegion.EWRAM_REGION:
                return self.ewram[address & MemoryRegion.EWRAM_MASK]
            case MemoryRegion.IWRAM_REGION:
                return self.iwram[address & MemoryRegion.IWRAM_MASK]
            case MemoryRegion.IO_REGION:
                # Not implemented, ignore instead of error
                return 0
            case MemoryRegion.PALRAM_REGION:
                return self.palram[address & MemoryRegion.PALRAM_MASK]
            case MemoryRegion.VRAM_REGION:
                mask = (MemoryRegion.VRAM_MASK_1 if get_bit(address, 4) else MemoryRegion.VRAM_MASK_2)
                return self.vram[address & mask]
            case MemoryRegion.OAM_REGION:
                return self.oam[address & MemoryRegion.OAM_MASK]
            case region if MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
                return self.gamepak.read_8(address)
            case MemoryRegion.SRAM_REGION:
                return self.gamepak.read_8(address)
            case _:
                raise NotImplementedError(f"Attempt to read from unused memory: {address:#010x}")

    def _write_32_internal(self, address: int, value: int):
        match address >> 24:
            case MemoryRegion.BIOS_REGION:
                # Ignore attempts to write to BIOS region
                pass
            case MemoryRegion.EWRAM_REGION:
                array_write_32(self.ewram, address & MemoryRegion.EWRAM_MASK, value)
            case MemoryRegion.IWRAM_REGION:
                array_write_32(self.iwram, address & MemoryRegion.IWRAM_MASK, value)
            case MemoryRegion.IO_REGION:
                # Not implemented, ignore instead of error
                pass
            case MemoryRegion.PALRAM_REGION:
                array_write_32(self.palram, address & MemoryRegion.PALRAM_MASK, value)
            case MemoryRegion.VRAM_REGION:
                mask = (MemoryRegion.VRAM_MASK_1 if get_bit(address, 4) else MemoryRegion.VRAM_MASK_2)
                array_write_32(self.vram, address & mask, value)
            case MemoryRegion.OAM_REGION:
                array_write_32(self.oam, address & MemoryRegion.OAM_MASK, value)
            case region if MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
                raise NotImplementedError
            case MemoryRegion.SRAM_REGION:
                raise NotImplementedError
            case _:
                raise NotImplementedError(f"Attempt to write to unused memory: {address:#010x}")

    def _write_16_internal(self, address: int, value: int):
        value = value & 0xFFFF
        match address >> 24:
            case MemoryRegion.BIOS_REGION:
                # Ignore attempts to write to BIOS region
                pass
            case MemoryRegion.EWRAM_REGION:
                array_write_16(self.ewram, address & MemoryRegion.EWRAM_MASK, value)
            case MemoryRegion.IWRAM_REGION:
                array_write_16(self.iwram, address & MemoryRegion.IWRAM_MASK, value)
            case MemoryRegion.IO_REGION:
                # Not implemented, ignore instead of error
                pass
            case MemoryRegion.PALRAM_REGION:
                array_write_16(self.palram, address & MemoryRegion.PALRAM_MASK, value)
            case MemoryRegion.VRAM_REGION:
                mask = (MemoryRegion.VRAM_MASK_1 if get_bit(address, 4) else MemoryRegion.VRAM_MASK_2)
                array_write_16(self.vram, address & mask, value)
            case MemoryRegion.OAM_REGION:
                array_write_16(self.oam, address & MemoryRegion.OAM_MASK, value)
            case region if MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
                raise NotImplementedError
            case MemoryRegion.SRAM_REGION:
                raise NotImplementedError
            case _:
                raise NotImplementedError(f"Attempt to write to unused memory: {address:#010x}")

    def _write_8_internal(self, address: int, value: int):
        value = value & 0xFF
        match address >> 24:
            case MemoryRegion.BIOS_REGION:
                # Ignore attempts to write to BIOS region
                pass
            case MemoryRegion.EWRAM_REGION:
                self.ewram[address & MemoryRegion.EWRAM_MASK] = value
            case MemoryRegion.IWRAM_REGION:
                self.iwram[address & MemoryRegion.IWRAM_MASK] = value
            case MemoryRegion.IO_REGION:
                # Not implemented, ignore instead of error
                pass
            case MemoryRegion.PALRAM_REGION:
                self.palram[address & MemoryRegion.PALRAM_MASK] = value
            case MemoryRegion.VRAM_REGION:
                mask = (MemoryRegion.VRAM_MASK_1 if get_bit(address, 4) else MemoryRegion.VRAM_MASK_2)
                self.vram[address & mask] = value
            case MemoryRegion.OAM_REGION:
                self.oam[address & MemoryRegion.OAM_MASK] = value
            case region if MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
                raise NotImplementedError
            case MemoryRegion.SRAM_REGION:
                raise NotImplementedError
            case _:
                raise NotImplementedError(f"Attempt to write to unused memory: {address:#010x}")

    def _add_cycles(self, address: int, access_type: MemoryAccess):
        pass
