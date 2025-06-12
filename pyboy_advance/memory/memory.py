from __future__ import annotations

from array import array
from enum import Enum
from typing import TYPE_CHECKING, Iterable

from pyboy_advance.cpu.constants import CPUState
from pyboy_advance.memory.constants import MemoryRegion
from pyboy_advance.memory.gamepak import GamePak
from pyboy_advance.memory.io import IO
from pyboy_advance.utils import (
    get_bit,
    array_read_16,
    array_read_32,
    array_write_32,
    array_write_16,
    ror_32,
    extend_sign_16,
    extend_sign_8,
)

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


class MemoryAccess(Enum):
    NON_SEQUENTIAL = 0
    SEQUENTIAL = 1


class Memory:
    def __init__(self, io: IO, gamepak: GamePak, bios: bytes | bytearray | Iterable[int]):
        self.cpu: CPU | None = None
        self.io = io

        # General Internal Memory
        self.bios = array("B", bios.ljust(MemoryRegion.BIOS_SIZE))
        self.ewram = array("B", [0] * MemoryRegion.EWRAM_SIZE)
        self.iwram = array("B", [0] * MemoryRegion.IWRAM_SIZE)

        # External Memory (Game Pak)
        self.gamepak = gamepak

        # If the program counter is not in the BIOS region, reading
        # BIOS will return the most recently fetched BIOS opcode,
        # which is tracked by this variable
        self.bios_last_opcode = 0

    def connect_cpu(self, cpu: CPU):
        self.cpu = cpu

    @property
    def irq_line(self) -> bool:
        return self.io.interrupt_controller.irq_line

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
        if get_bit(address, 0):
            return self.read_8_signed(address, access_type)
        return extend_sign_16(self.read_16(address, access_type))

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
        address = address & ~0b11  # Align address to 4-byte boundary
        region = address >> 24

        if region == MemoryRegion.BIOS_REGION:
            if address <= MemoryRegion.BIOS_END:
                if not self.cpu or self.cpu.regs.pc <= MemoryRegion.BIOS_END:
                    self.bios_last_opcode = array_read_32(
                        self.bios, address & MemoryRegion.BIOS_MASK
                    )
                return self.bios_last_opcode
            return self._read_unused_memory()

        elif region == MemoryRegion.EWRAM_REGION:
            return array_read_32(self.ewram, address & MemoryRegion.EWRAM_MASK)

        elif region == MemoryRegion.IWRAM_REGION:
            return array_read_32(self.iwram, address & MemoryRegion.IWRAM_MASK)

        elif MemoryRegion.IO_START <= address <= MemoryRegion.IO_END:
            return self.io.read_32(address)

        elif region == MemoryRegion.PALRAM_REGION:
            return array_read_32(self.io.ppu.palram, address & MemoryRegion.PALRAM_MASK)

        elif region == MemoryRegion.VRAM_REGION:
            mask = self._get_vram_address_mask(address)
            return array_read_32(self.io.ppu.vram, address & mask)

        elif region == MemoryRegion.OAM_REGION:
            return array_read_32(self.io.ppu.oam, address & MemoryRegion.OAM_MASK)

        elif MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
            return self.gamepak.read_32(address)

        elif region == MemoryRegion.SRAM_REGION:
            return self.gamepak.read_32(address)

        else:
            return self._read_unused_memory()

    def _read_16_internal(self, address: int) -> int:
        address = address & ~0b1  # Align address to 2-byte boundary
        region = address >> 24

        if region == MemoryRegion.BIOS_REGION:
            if address <= MemoryRegion.BIOS_END:
                if not self.cpu or self.cpu.regs.pc <= MemoryRegion.BIOS_END:
                    return array_read_16(self.bios, address & MemoryRegion.BIOS_MASK)
                return (self.bios_last_opcode >> ((address & 2) << 3)) & 0xFFFF
            return (self._read_unused_memory() >> ((address & 2) << 3)) & 0xFFFF

        elif region == MemoryRegion.EWRAM_REGION:
            return array_read_16(self.ewram, address & MemoryRegion.EWRAM_MASK)

        elif region == MemoryRegion.IWRAM_REGION:
            return array_read_16(self.iwram, address & MemoryRegion.IWRAM_MASK)

        elif MemoryRegion.IO_START <= address <= MemoryRegion.IO_END:
            return self.io.read_16(address)

        elif region == MemoryRegion.PALRAM_REGION:
            return array_read_16(self.io.ppu.palram, address & MemoryRegion.PALRAM_MASK)

        elif region == MemoryRegion.VRAM_REGION:
            mask = self._get_vram_address_mask(address)
            return array_read_16(self.io.ppu.vram, address & mask)

        elif region == MemoryRegion.OAM_REGION:
            return array_read_16(self.io.ppu.oam, address & MemoryRegion.OAM_MASK)

        elif MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
            return self.gamepak.read_16(address)

        elif region == MemoryRegion.SRAM_REGION:
            return self.gamepak.read_16(address)

        else:
            return (self._read_unused_memory() >> ((address & 2) << 3)) & 0xFFFF

    def _read_8_internal(self, address: int) -> int:
        region = address >> 24

        if region == MemoryRegion.BIOS_REGION:
            if address <= MemoryRegion.BIOS_END:
                if not self.cpu or self.cpu.regs.pc <= MemoryRegion.BIOS_END:
                    return self.bios[address & MemoryRegion.BIOS_MASK]
                return (self.bios_last_opcode >> ((address & 3) << 3)) & 0xFF
            return (self._read_unused_memory() >> ((address & 3) << 3)) & 0xFF

        elif region == MemoryRegion.EWRAM_REGION:
            return self.ewram[address & MemoryRegion.EWRAM_MASK]

        elif region == MemoryRegion.IWRAM_REGION:
            return self.iwram[address & MemoryRegion.IWRAM_MASK]

        elif MemoryRegion.IO_START <= address <= MemoryRegion.IO_END:
            return self.io.read_8(address)

        elif region == MemoryRegion.PALRAM_REGION:
            return self.io.ppu.palram[address & MemoryRegion.PALRAM_MASK]

        elif region == MemoryRegion.VRAM_REGION:
            mask = self._get_vram_address_mask(address)
            return self.io.ppu.vram[address & mask]

        elif region == MemoryRegion.OAM_REGION:
            return self.io.ppu.oam[address & MemoryRegion.OAM_MASK]

        elif MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
            return self.gamepak.read_8(address)

        elif region == MemoryRegion.SRAM_REGION:
            return self.gamepak.read_8(address)

        else:
            return (self._read_unused_memory() >> ((address & 3) << 3)) & 0xFF

    def _write_32_internal(self, address: int, value: int):
        address = address & ~0b11  # Align address to 4-byte boundary
        region = address >> 24

        if region == MemoryRegion.BIOS_REGION:
            # Ignore attempts to write to BIOS region
            pass

        elif region == MemoryRegion.EWRAM_REGION:
            array_write_32(self.ewram, address & MemoryRegion.EWRAM_MASK, value)

        elif region == MemoryRegion.IWRAM_REGION:
            array_write_32(self.iwram, address & MemoryRegion.IWRAM_MASK, value)

        elif region == MemoryRegion.IO_REGION:
            self.io.write_32(address, value)

        elif region == MemoryRegion.PALRAM_REGION:
            array_write_32(self.io.ppu.palram, address & MemoryRegion.PALRAM_MASK, value)

        elif region == MemoryRegion.VRAM_REGION:
            mask = self._get_vram_address_mask(address)
            array_write_32(self.io.ppu.vram, address & mask, value)

        elif region == MemoryRegion.OAM_REGION:
            array_write_32(self.io.ppu.oam, address & MemoryRegion.OAM_MASK, value)

        elif MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
            raise NotImplementedError

        elif region == MemoryRegion.SRAM_REGION:
            raise NotImplementedError

        else:
            print(f"Attempt to write to unused memory: {address:#010x}")

    def _write_16_internal(self, address: int, value: int):
        address = address & ~0b1  # Align address to 2-byte boundary
        value = value & 0xFFFF
        region = address >> 24

        if region == MemoryRegion.BIOS_REGION:
            # Ignore attempts to write to BIOS region
            pass

        elif region == MemoryRegion.EWRAM_REGION:
            array_write_16(self.ewram, address & MemoryRegion.EWRAM_MASK, value)

        elif region == MemoryRegion.IWRAM_REGION:
            array_write_16(self.iwram, address & MemoryRegion.IWRAM_MASK, value)

        elif region == MemoryRegion.IO_REGION:
            self.io.write_16(address, value)

        elif region == MemoryRegion.PALRAM_REGION:
            array_write_16(self.io.ppu.palram, address & MemoryRegion.PALRAM_MASK, value)

        elif region == MemoryRegion.VRAM_REGION:
            mask = self._get_vram_address_mask(address)
            array_write_16(self.io.ppu.vram, address & mask, value)

        elif region == MemoryRegion.OAM_REGION:
            array_write_16(self.io.ppu.oam, address & MemoryRegion.OAM_MASK, value)

        elif MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
            raise NotImplementedError

        elif region == MemoryRegion.SRAM_REGION:
            raise NotImplementedError

        else:
            print(f"Attempt to write to unused memory: {address:#010x}")

    def _write_8_internal(self, address: int, value: int):
        value = value & 0xFF
        region = address >> 24

        if region == MemoryRegion.BIOS_REGION:
            # Ignore attempts to write to BIOS region
            pass

        elif region == MemoryRegion.EWRAM_REGION:
            self.ewram[address & MemoryRegion.EWRAM_MASK] = value

        elif region == MemoryRegion.IWRAM_REGION:
            self.iwram[address & MemoryRegion.IWRAM_MASK] = value

        elif region == MemoryRegion.IO_REGION:
            self.io.write_8(address, value)

        elif region == MemoryRegion.PALRAM_REGION:
            # Writing a byte to PALRAM writes the value to both the upper and lower 8-bits
            # of the addressed halfword
            address = address & ~0b1  # Align address to 2-byte boundary
            self.io.ppu.palram[address & MemoryRegion.PALRAM_MASK] = value
            self.io.ppu.palram[(address + 1) & MemoryRegion.PALRAM_MASK] = value

        elif region == MemoryRegion.VRAM_REGION:
            # VRAM is split into BG and OBJ regions.
            # Size of the BG region changes depending on whether we are in bitmap mode
            video_mode = self.io.ppu.display_control.video_mode
            bg_region_end = 0x14000 if video_mode.bitmapped else 0x10000

            # Ignore attempts to write a byte into OBJ, but allow writes into BG
            if address & 0x1FFFF < bg_region_end:
                # Writing a byte to BG writes the value to both the upper and lower 8-bits
                # of the addressed halfword
                address = address & ~0b1  # Align address to 2-byte boundary
                mask_1 = self._get_vram_address_mask(address)
                mask_2 = self._get_vram_address_mask(address + 1)
                self.io.ppu.vram[address & mask_1] = value
                self.io.ppu.vram[(address + 1) & mask_2] = value

        elif region == MemoryRegion.OAM_REGION:
            # Ignore attempts to write a byte into OAM
            pass

        elif MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
            raise NotImplementedError

        elif region == MemoryRegion.SRAM_REGION:
            raise NotImplementedError

        else:
            print(f"Attempt to write to unused memory: {address:#010x}")

    def _read_unused_memory(self) -> int:
        """
        Reading from unused memory returns the last prefetched instruction.
        https://problemkaputt.de/gbatek.htm#gbaunpredictablethings

        For THUMB code, the result consists of two 16-bit fragments and depends on
        the address area and alignment where the opcode was stored.
        """
        if self.cpu.regs.cpsr.state == CPUState.ARM:
            return self.cpu.pipeline[1]

        region = self.cpu.regs.pc >> 24

        if region == MemoryRegion.BIOS_REGION or region == MemoryRegion.OAM_REGION:
            if (self.cpu.regs.pc & 0b11) == 0:
                # According to GBATEK, we should be using [$+6] for the top 16 bits
                # here, but that isn't prefetched yet?
                return (self.cpu.pipeline[1] << 16) | self.cpu.pipeline[1]
            else:
                return (self.cpu.pipeline[1] << 16) | self.cpu.pipeline[0]

        elif region == MemoryRegion.IWRAM_REGION:
            if (self.cpu.regs.pc & 0b11) == 0:
                return (self.cpu.pipeline[0] << 16) | self.cpu.pipeline[1]
            else:
                return (self.cpu.pipeline[1] << 16) | self.cpu.pipeline[0]

        else:
            return (self.cpu.pipeline[1] << 16) | self.cpu.pipeline[1]

    @staticmethod
    def _get_vram_address_mask(address: int) -> int:
        """
        Get the appropriate mask for the given VRAM address.

        GBA VRAM is 96 KB (64K + 32K) but is mirrored in 128 KB steps
        (64K + 32K + 32K, the two 32K blocks being mirrors of each other).

        Hence, if the address is in the mirrored upper region (bit 16 set), we use
        VRAM_MASK_1 to wrap it back into valid VRAM space. Otherwise, we use VRAM_MASK_2.
        """
        return MemoryRegion.VRAM_MASK_1 if get_bit(address, 16) else MemoryRegion.VRAM_MASK_2

    def _add_cycles(self, address: int, access_type: MemoryAccess):
        pass
