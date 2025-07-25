from __future__ import annotations

from array import array
from typing import TYPE_CHECKING, Iterable

from pyboy_advance.cpu.constants import CPUState
from pyboy_advance.interrupt_controller import PowerDownMode
from pyboy_advance.memory.constants import MemoryRegion, MemoryAccess
from pyboy_advance.memory.gamepak import GamePak
from pyboy_advance.memory.io import IO
from pyboy_advance.scheduler import Scheduler
from pyboy_advance.utils import (
    get_bit,
    array_read_16,
    array_read_32,
    array_write_32,
    array_write_16,
    ror_32,
    extend_sign_16,
    extend_sign_8,
    get_bits,
)

if TYPE_CHECKING:
    from pyboy_advance.cpu.cpu import CPU


class Memory:
    def __init__(
        self,
        scheduler: Scheduler,
        gamepak: GamePak,
        bios: bytes | bytearray | Iterable[int],
    ):
        self.scheduler = scheduler
        self.cpu: CPU | None = None
        self.io: IO | None = None

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

        self.wait_control = WaitstateControlRegister()

        self._init_access_times()

    @property
    def irq_line(self) -> bool:
        return self.io.interrupt_controller.irq_line

    @property
    def power_down_mode(self) -> PowerDownMode:
        return self.io.interrupt_controller.power_down_mode

    def read_32(self, address: int, access_type: MemoryAccess) -> int:
        return self._read_32_internal(address, access_type)

    def read_32_ror(self, address: int, access_type: MemoryAccess) -> int:
        value = self.read_32(address, access_type)
        rotate = (address & 0b11) * 8
        return ror_32(value, rotate)

    def read_16(self, address: int, access_type: MemoryAccess) -> int:
        return self._read_16_internal(address, access_type)

    def read_16_signed(self, address: int, access_type: MemoryAccess) -> int:
        if get_bit(address, 0):
            return self.read_8_signed(address, access_type)
        return extend_sign_16(self.read_16(address, access_type))

    def read_16_ror(self, address: int, access_type: MemoryAccess) -> int:
        value = self.read_16(address, access_type)
        rotate = (address & 0b1) * 8
        return ror_32(value, rotate)

    def read_8(self, address: int, access_type: MemoryAccess) -> int:
        return self._read_8_internal(address, access_type)

    def read_8_signed(self, address: int, access_type: MemoryAccess) -> int:
        value = self.read_8(address, access_type)
        return extend_sign_8(value)

    def write_32(self, address: int, value: int, access_type: MemoryAccess):
        self._write_32_internal(address, value, access_type)

    def write_16(self, address: int, value: int, access_type: MemoryAccess):
        self._write_16_internal(address, value, access_type)

    def write_8(self, address: int, value: int, access_type: MemoryAccess):
        self._write_8_internal(address, value, access_type)

    def _read_32_internal(self, address: int, access_type: MemoryAccess) -> int:
        self._idle_for_access(address, 4, access_type)

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
            return self.io.ppu.memory.read_32_palram(address)

        elif region == MemoryRegion.VRAM_REGION:
            return self.io.ppu.memory.read_32_vram(address)

        elif region == MemoryRegion.OAM_REGION:
            return self.io.ppu.memory.read_32_oam(address)

        elif MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
            return self.gamepak.read_32(address)

        elif region == MemoryRegion.SRAM_REGION:
            print(f"Attempt to read SRAM: {address:#010x}")
            return 0

        else:
            return self._read_unused_memory()

    def _read_16_internal(self, address: int, access_type: MemoryAccess) -> int:
        self._idle_for_access(address, 2, access_type)

        address = address & ~0b1  # Align address to 2-byte boundary
        region = address >> 24

        if region == MemoryRegion.BIOS_REGION:
            if address <= MemoryRegion.BIOS_END:
                if not self.cpu or self.cpu.regs.pc <= MemoryRegion.BIOS_END:
                    self.bios_last_opcode = array_read_32(
                        self.bios, address & ~0b11 & MemoryRegion.BIOS_MASK
                    )
                return (self.bios_last_opcode >> ((address & 0b11) * 8)) & 0xFFFF
            return (self._read_unused_memory() >> ((address & 0b11) * 8)) & 0xFFFF

        elif region == MemoryRegion.EWRAM_REGION:
            return array_read_16(self.ewram, address & MemoryRegion.EWRAM_MASK)

        elif region == MemoryRegion.IWRAM_REGION:
            return array_read_16(self.iwram, address & MemoryRegion.IWRAM_MASK)

        elif MemoryRegion.IO_START <= address <= MemoryRegion.IO_END:
            return self.io.read_16(address)

        elif region == MemoryRegion.PALRAM_REGION:
            return self.io.ppu.memory.read_16_palram(address)

        elif region == MemoryRegion.VRAM_REGION:
            return self.io.ppu.memory.read_16_vram(address)

        elif region == MemoryRegion.OAM_REGION:
            return self.io.ppu.memory.read_16_oam(address)

        elif MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
            return self.gamepak.read_16(address)

        elif region == MemoryRegion.SRAM_REGION:
            print(f"Attempt to read SRAM: {address:#010x}")
            return 0

        else:
            return (self._read_unused_memory() >> ((address & 0b11) * 8)) & 0xFFFF

    def _read_8_internal(self, address: int, access_type: MemoryAccess) -> int:
        self._idle_for_access(address, 1, access_type)

        region = address >> 24

        if region == MemoryRegion.BIOS_REGION:
            if address <= MemoryRegion.BIOS_END:
                if not self.cpu or self.cpu.regs.pc <= MemoryRegion.BIOS_END:
                    self.bios_last_opcode = array_read_32(
                        self.bios, address & ~0b11 & MemoryRegion.BIOS_MASK
                    )
                return (self.bios_last_opcode >> ((address & 0b11) * 8)) & 0xFF
            return (self._read_unused_memory() >> ((address & 0b11) * 8)) & 0xFF

        elif region == MemoryRegion.EWRAM_REGION:
            return self.ewram[address & MemoryRegion.EWRAM_MASK]

        elif region == MemoryRegion.IWRAM_REGION:
            return self.iwram[address & MemoryRegion.IWRAM_MASK]

        elif MemoryRegion.IO_START <= address <= MemoryRegion.IO_END:
            return self.io.read_8(address)

        elif region == MemoryRegion.PALRAM_REGION:
            return self.io.ppu.memory.read_8_palram(address)

        elif region == MemoryRegion.VRAM_REGION:
            return self.io.ppu.memory.read_8_vram(address)

        elif region == MemoryRegion.OAM_REGION:
            return self.io.ppu.memory.read_8_oam(address)

        elif MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
            return self.gamepak.read_8(address)

        elif region == MemoryRegion.SRAM_REGION:
            print(f"Attempt to read SRAM: {address:#010x}")
            return 0

        else:
            return (self._read_unused_memory() >> ((address & 0b11) * 8)) & 0xFF

    def _write_32_internal(self, address: int, value: int, access_type: MemoryAccess):
        self._idle_for_access(address, 4, access_type)

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
            self.io.ppu.memory.write_32_palram(address, value)

        elif region == MemoryRegion.VRAM_REGION:
            self.io.ppu.memory.write_32_vram(address, value)

        elif region == MemoryRegion.OAM_REGION:
            self.io.ppu.memory.write_32_oam(address, value)

        elif MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
            print(f"Attempt to write to SRAM: {address:#010x}")

        elif region == MemoryRegion.SRAM_REGION:
            print(f"Attempt to write to SRAM: {address:#010x}")

        else:
            print(f"Attempt to write to unused memory: {address:#010x}")

    def _write_16_internal(self, address: int, value: int, access_type: MemoryAccess):
        self._idle_for_access(address, 2, access_type)

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
            self.io.ppu.memory.write_16_palram(address, value)

        elif region == MemoryRegion.VRAM_REGION:
            self.io.ppu.memory.write_16_vram(address, value)

        elif region == MemoryRegion.OAM_REGION:
            self.io.ppu.memory.write_16_oam(address, value)

        elif MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
            print(f"Attempt to write to SRAM: {address:#010x}")

        elif region == MemoryRegion.SRAM_REGION:
            print(f"Attempt to write to SRAM: {address:#010x}")

        else:
            print(f"Attempt to write to unused memory: {address:#010x}")

    def _write_8_internal(self, address: int, value: int, access_type: MemoryAccess):
        self._idle_for_access(address, 1, access_type)

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
            self.io.ppu.memory.write_8_palram(address, value)

        elif region == MemoryRegion.VRAM_REGION:
            self.io.ppu.memory.write_8_vram(address, value)

        elif region == MemoryRegion.OAM_REGION:
            # Ignore attempts to write a byte into OAM
            pass

        elif MemoryRegion.GAMEPAK_REGION_START <= region <= MemoryRegion.GAMEPAK_REGION_END:
            print(f"Attempt to write to SRAM: {address:#010x}")

        elif region == MemoryRegion.SRAM_REGION:
            print(f"Attempt to write to SRAM: {address:#010x}")

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

    def _init_access_times(self):
        """
        Source: GBATEK

        Region        Bus   Read      Write     Cycles
        =====================================================
        BIOS ROM      32    8/16/32   -         1/1/1
        Work RAM 32K  32    8/16/32   8/16/32   1/1/1
        I/O           32    8/16/32   8/16/32   1/1/1
        OAM           32    8/16/32   16/32     1/1/1 *
        Work RAM 256K 16    8/16/32   8/16/32   3/3/6 **
        Palette RAM   16    8/16/32   16/32     1/1/2 *
        VRAM          16    8/16/32   16/32     1/1/2 *
        GamePak ROM   16    8/16/32   -         5/5/8 **/***
        GamePak Flash 16    8/16/32   16/32     5/5/8 **/***
        GamePak SRAM  8     8         8         5     **

        Timing Notes:

          *   Plus 1 cycle if GBA accesses video memory at the same time.
          **  Default waitstate settings, see System Control chapter.
          *** Separate timings for sequential, and non-sequential accesses.

        """
        # fmt: off
        self.access_time_32 = [[1] * 0x10 for _ in range(len(MemoryAccess))]
        self.access_time_16 = [[1] * 0x10 for _ in range(len(MemoryAccess))]

        self.access_time_32[MemoryAccess.NON_SEQUENTIAL][MemoryRegion.EWRAM_REGION]  = 6
        self.access_time_32[MemoryAccess.SEQUENTIAL][MemoryRegion.EWRAM_REGION]      = 6
        self.access_time_16[MemoryAccess.NON_SEQUENTIAL][MemoryRegion.EWRAM_REGION]  = 3
        self.access_time_16[MemoryAccess.SEQUENTIAL][MemoryRegion.EWRAM_REGION]      = 3

        self.access_time_32[MemoryAccess.NON_SEQUENTIAL][MemoryRegion.PALRAM_REGION] = 2
        self.access_time_32[MemoryAccess.SEQUENTIAL][MemoryRegion.PALRAM_REGION]     = 2

        self.access_time_32[MemoryAccess.NON_SEQUENTIAL][MemoryRegion.VRAM_REGION]   = 2
        self.access_time_32[MemoryAccess.SEQUENTIAL][MemoryRegion.VRAM_REGION]       = 2

        self.access_time_32[MemoryAccess.NON_SEQUENTIAL][MemoryRegion.OAM_REGION]    = 2
        self.access_time_32[MemoryAccess.SEQUENTIAL][MemoryRegion.OAM_REGION]        = 2

        self.update_waitstates()
        # fmt: on

    def update_waitstates(self):
        # fmt: off
        self.access_time_16[MemoryAccess.NON_SEQUENTIAL][MemoryRegion.GAMEPAK_0_REGION_1] = 1 + self.wait_control.ws0_non_seq
        self.access_time_16[MemoryAccess.NON_SEQUENTIAL][MemoryRegion.GAMEPAK_0_REGION_2] = 1 + self.wait_control.ws0_non_seq
        self.access_time_16[MemoryAccess.NON_SEQUENTIAL][MemoryRegion.GAMEPAK_1_REGION_1] = 1 + self.wait_control.ws1_non_seq
        self.access_time_16[MemoryAccess.NON_SEQUENTIAL][MemoryRegion.GAMEPAK_1_REGION_2] = 1 + self.wait_control.ws1_non_seq
        self.access_time_16[MemoryAccess.NON_SEQUENTIAL][MemoryRegion.GAMEPAK_2_REGION_1] = 1 + self.wait_control.ws2_non_seq
        self.access_time_16[MemoryAccess.NON_SEQUENTIAL][MemoryRegion.GAMEPAK_2_REGION_2] = 1 + self.wait_control.ws2_non_seq
        self.access_time_16[MemoryAccess.NON_SEQUENTIAL][MemoryRegion.SRAM_REGION]        = 1 + self.wait_control.sram

        self.access_time_16[MemoryAccess.SEQUENTIAL][MemoryRegion.GAMEPAK_0_REGION_1] = 1 + self.wait_control.ws0_seq
        self.access_time_16[MemoryAccess.SEQUENTIAL][MemoryRegion.GAMEPAK_0_REGION_2] = 1 + self.wait_control.ws0_seq
        self.access_time_16[MemoryAccess.SEQUENTIAL][MemoryRegion.GAMEPAK_1_REGION_1] = 1 + self.wait_control.ws1_seq
        self.access_time_16[MemoryAccess.SEQUENTIAL][MemoryRegion.GAMEPAK_1_REGION_2] = 1 + self.wait_control.ws1_seq
        self.access_time_16[MemoryAccess.SEQUENTIAL][MemoryRegion.GAMEPAK_2_REGION_1] = 1 + self.wait_control.ws2_seq
        self.access_time_16[MemoryAccess.SEQUENTIAL][MemoryRegion.GAMEPAK_2_REGION_2] = 1 + self.wait_control.ws2_seq
        self.access_time_16[MemoryAccess.SEQUENTIAL][MemoryRegion.SRAM_REGION]        = 1 + self.wait_control.sram
        # fmt: on

        for region in range(MemoryRegion.GAMEPAK_0_REGION_1, MemoryRegion.SRAM_REGION + 1):
            self.access_time_32[MemoryAccess.NON_SEQUENTIAL][region] = (
                self.access_time_16[MemoryAccess.NON_SEQUENTIAL][region]
                + self.access_time_16[MemoryAccess.SEQUENTIAL][region]
            )
            self.access_time_32[MemoryAccess.SEQUENTIAL][region] = (
                self.access_time_16[MemoryAccess.SEQUENTIAL][region] * 2
            )

    def _idle_for_access(self, address: int, size: int, access_type: MemoryAccess):
        region = (address >> 24) & 0xF

        cycles = (
            self.access_time_32[access_type][region]
            if size == 4
            else self.access_time_16[access_type][region]
        )

        self.scheduler.idle(cycles)


class WaitstateControlRegister:
    NON_SEQUENTIAL_CYCLES = [4, 3, 2, 8]

    def __init__(self):
        self.reg = 0

    @property
    def sram(self):
        return self.NON_SEQUENTIAL_CYCLES[get_bits(self.reg, 0, 1)]

    @property
    def ws0_non_seq(self):
        return self.NON_SEQUENTIAL_CYCLES[get_bits(self.reg, 2, 3)]

    @property
    def ws0_seq(self):
        return 1 if get_bit(self.reg, 4) else 2

    @property
    def ws1_non_seq(self):
        return self.NON_SEQUENTIAL_CYCLES[get_bits(self.reg, 5, 6)]

    @property
    def ws1_seq(self):
        return 1 if get_bit(self.reg, 7) else 4

    @property
    def ws2_non_seq(self):
        return self.NON_SEQUENTIAL_CYCLES[get_bits(self.reg, 8, 9)]

    @property
    def ws2_seq(self):
        return 1 if get_bit(self.reg, 10) else 8
    