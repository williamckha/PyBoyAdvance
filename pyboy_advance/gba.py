import argparse
import os

from pyboy_advance.cpu.cpu import CPU
from pyboy_advance.cpu.registers import BankIndex
from pyboy_advance.memory.gamepak import GamePak
from pyboy_advance.memory.io import IO
from pyboy_advance.memory.memory import Memory
from pyboy_advance.ppu.ppu import PPU


class GBA:
    def __init__(self, gamepak: GamePak | str | os.PathLike, skip_bios: bool = False):
        self.gamepak = (
            GamePak.from_file(gamepak) if isinstance(gamepak, (str, os.PathLike)) else gamepak
        )

        self.ppu = PPU()
        self.io = IO(self.ppu)
        self.memory = Memory(self.io, self.gamepak)
        self.cpu = CPU(self.memory)

        if skip_bios:
            self.cpu.regs.banked_sp[BankIndex.SYSTEM_USER] = 0x03007F00
            self.cpu.regs.banked_sp[BankIndex.FIQ] = 0x03007F00
            self.cpu.regs.banked_sp[BankIndex.IRQ] = 0x03007FA0
            self.cpu.regs.banked_sp[BankIndex.SWI] = 0x03007FE0
            self.cpu.regs.banked_sp[BankIndex.ABORT] = 0x03007F00
            self.cpu.regs.banked_sp[BankIndex.UNDEFINED] = 0x03007F00
            self.cpu.regs.sp = 0x03007F00
            self.cpu.regs.pc = 0x08000000
            self.cpu.flush_pipeline()

    def step(self):
        self.cpu.step()
        self.ppu.draw()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("pyboy_advance")
    parser.add_argument("rom", type=str)
    args = parser.parse_args()

    gba = GBA(args.rom, skip_bios=True)
    while True:
        gba.step()
