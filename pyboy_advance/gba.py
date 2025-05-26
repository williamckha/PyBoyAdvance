import argparse
import os

from pyboy_advance.cpu.cpu import CPU
from pyboy_advance.cpu.registers import BankIndex
from pyboy_advance.memory.gamepak import GamePak
from pyboy_advance.memory.memory import Memory


class GBA:

    def __init__(self, gamepak: GamePak | str | os.PathLike, skip_bios: bool = False):
        self.gamepak = (
            GamePak.from_file(gamepak)
            if isinstance(gamepak, (str, os.PathLike)) else
            gamepak
        )

        self.memory = Memory(self.gamepak)
        self.cpu = CPU(self.memory)

        if skip_bios:
            self.cpu.regs.banked_sp[BankIndex.SYSTEM_USER] = 0x03007f00
            self.cpu.regs.banked_sp[BankIndex.FIQ] = 0x03007f00
            self.cpu.regs.banked_sp[BankIndex.IRQ] = 0x03007fa0
            self.cpu.regs.banked_sp[BankIndex.SWI] = 0x03007fe0
            self.cpu.regs.banked_sp[BankIndex.ABORT] = 0x03007f00
            self.cpu.regs.banked_sp[BankIndex.UNDEFINED] = 0x03007f00
            self.cpu.regs.sp = 0x03007f00
            self.cpu.regs.pc = 0x08000000
            self.cpu.flush_pipeline()

    def step(self):
        self.cpu.step()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("pyboy_advance")
    parser.add_argument("rom", type=str)
    args = parser.parse_args()

    gba = GBA(args.rom, skip_bios=True)

    for i in range(1000):
        gba.step()
