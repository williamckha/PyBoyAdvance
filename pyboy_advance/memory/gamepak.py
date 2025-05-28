from __future__ import annotations

import os
from array import array
from typing import Iterable

from pyboy_advance.memory.constants import MemoryRegion
from pyboy_advance.utils import array_read_32, array_read_16


class GamePak:

    @staticmethod
    def from_file(rom_file_path: str | os.PathLike) -> GamePak:
        with open(rom_file_path, "rb") as rom_file:
            rom_bytes = bytearray(rom_file.read())
            return GamePak(rom_bytes)

    def __init__(self, rom: bytes | bytearray | Iterable[int]):
        self.rom = array("B", rom.ljust(MemoryRegion.GAMEPAK_SIZE))

    def read_32(self, address: int) -> int:
        return array_read_32(self.rom, address & MemoryRegion.GAMEPAK_MASK)

    def read_16(self, address: int) -> int:
        return array_read_16(self.rom, address & MemoryRegion.GAMEPAK_MASK)

    def read_8(self, address: int) -> int:
        return self.rom[address & MemoryRegion.GAMEPAK_MASK]
