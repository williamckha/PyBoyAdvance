import argparse
import os
import traceback

from pyboy_advance.cpu.cpu import CPU
from pyboy_advance.cpu.registers import BankIndex
from pyboy_advance.memory.gamepak import GamePak
from pyboy_advance.memory.io import IO
from pyboy_advance.memory.memory import Memory, MemoryAccess
from pyboy_advance.ppu.ppu import PPU


class GBA:

    def __init__(self, gamepak: GamePak | str | os.PathLike, skip_bios: bool = False):
        self.gamepak = (
            GamePak.from_file(gamepak)
            if isinstance(gamepak, (str, os.PathLike)) else
            gamepak
        )

        self.ppu = PPU()
        self.io = IO(self.ppu)
        self.memory = Memory(self.io, self.gamepak)
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
        self.ppu.draw()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("pyboy_advance")
    parser.add_argument("rom", type=str)
    args = parser.parse_args()

    gba = GBA(args.rom, skip_bios=True)

    instruction_count = 0

    try:
        instruction = 0
        while instruction != 0b11101010111111111111111111111110:
            instruction = gba.memory.read_32(gba.cpu.regs.pc - 8, MemoryAccess.SEQUENTIAL)
            instruction_count += 1
            gba.step()
    except Exception as e:
        print(traceback.format_exc())

    print("Instruction count: ", instruction_count)

    assert gba.cpu.regs[12] == 0, f"Failed test {gba.cpu.regs[12]:03}"

    print("Success! All tests passed")